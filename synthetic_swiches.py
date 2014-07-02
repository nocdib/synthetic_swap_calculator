import datetime
import uuid

def ilog(indent, s):
  print((' ' * 2 * indent) + s)

class Order(dict):
  def __init__(self, d):
    self.update(d)
    self['id'] = uuid.uuid4()
    self['time'] = datetime.datetime.now()

  def short_id(self):
    return str(self['id'])[:8]

  def __str__(self):
    if self['syn']:
      syn = 'syn(%s %s %s)' % (self['lhs'], self['op'], self['rhs'])
    else:
      syn = 'real'
    return '(%s,%s,%s,%s,%s,%s,%s)' % (
        self.short_id(),
        self['book'],
        self['side'],
        self['price'],
        self['user'],
        self['time'],
        syn
      )
    
class Book():
  use_cache = True
  
  def __init__(self, id):
    self.id = id
    self.bid = []
    self.ask = []
    self.lhs = None
    self.rhs = None
    self.lhs_switches = []
    self.rhs_switches = []
    self.cache = {}
    
  def cache_it(self, k, v):
    self.cache[k] = v
    return v
    
  def best_bid(self, chain=set(), ind=0):
    if Book.use_cache and 'best_bid' in self.cache: return self.cache['best_bid']
    ilog(ind, '%s.best_bid(%s)' % (self.id, chain))
    real = self.bid[0] if self.bid else None
    syn = self.best_syn_bid(chain=chain, ind=ind+1) if not self.id in chain else None
    return self.cache_it('best_bid', best_bid(real, syn))
  def best_ask(self, chain=set(), ind=0):
    if Book.use_cache and 'best_ask' in self.cache: return self.cache['best_ask']
    ilog(ind, '%s.best_ask(%s)' % (self.id, chain))
    real = self.ask[0] if self.ask else None
    syn = self.best_syn_ask(chain=chain, ind=ind+1) if not self.id in chain else None
    return self.cache_it('best_ask', best_ask(real, syn))
    
  def best_syn_bid(self, chain=set(), ind=0):
    if Book.use_cache and 'best_syn_bid' in self.cache: return self.cache['best_syn_bid']
    ilog(ind, '%s.best_syn_bid(%s)' % (self.id, chain))
    if self.lhs and self.rhs:
      lhs_ask = self.lhs.best_ask(chain=(chain | set([self.id])), ind=ind+1)
      rhs_bid = self.rhs.best_bid(chain=(chain | set([self.id])), ind=ind+1)
      if lhs_ask and rhs_bid:
        return self.cache_it('best_syn_bid', Order({
          'book' : self.id,
          'side' : 'bid',
          'price' : rhs_bid['price'] - lhs_ask['price'],
          'user' : None,
          'syn' : True,
          'lhs' : (self.rhs.id, rhs_bid['price']),
          'op' : '-',
          'rhs' : (self.lhs.id, lhs_ask['price'])
        }))
      else: return self.cache_it('best_syn_bid', None)
    else:
      best = None
      for s in self.lhs_switches:
        s_best_ask = s.best_ask(chain=(chain | set([self.id])), ind=ind+1)
        rhs_best_bid = s.rhs.best_bid(chain=(chain | set([self.id])), ind=ind+1)  
        if s_best_ask and rhs_best_bid:
          syn = Order({
            'book' : self.id,
            'side' : 'bid',
            'price' : rhs_best_bid['price'] - s_best_ask['price'],
            'user' : None,
            'syn' : True,
            'lhs' : (s.rhs.id, rhs_best_bid['price']),
            'op' : '-',
            'rhs' : (s.id, s_best_ask['price'])
          })
          if not best or better('bid', syn, best):
            best = syn 
      for s in self.rhs_switches:
        s_best_bid = s.best_bid(chain=(chain | set([self.id])), ind=ind+1)
        lhs_best_bid = s.lhs.best_bid(chain=(chain | set([self.id])), ind=ind+1)  
        if s_best_bid and lhs_best_bid:
          syn = Order({
            'book' : self.id,
            'side' : 'bid',
            'price' : lhs_best_bid['price'] + s_best_bid['price'],
            'user' : None,
            'syn' : True,
            'lhs' : (s.lhs.id, lhs_best_bid['price']),
            'op' : '+',
            'rhs' : (s.id, s_best_bid['price'])
          })
          if not best or better('bid', syn, best):
            best = syn
      return self.cache_it('best_syn_bid', best)
          
  def best_syn_ask(self, chain=set(), ind=0):
    if Book.use_cache and 'best_syn_ask' in self.cache: return self.cache['best_syn_ask']
    ilog(ind, '%s.best_syn_ask(%s)' % (self.id, chain))
    if self.lhs and self.rhs:
      lhs_bid = self.lhs.best_bid(chain=(chain | set([self.id])), ind=ind+1)
      rhs_ask = self.rhs.best_ask(chain=(chain | set([self.id])), ind=ind+1)
      if lhs_bid and rhs_ask:
        return self.cache_it('best_syn_ask', Order({
          'book' : self.id,
          'side' : 'ask',
          'price' : rhs_ask['price'] - lhs_bid['price'],
          'user' : None,
          'syn' : True,
          'lhs' : (self.rhs.id, rhs_ask['price']),
          'op' : '-',
          'rhs' : (self.lhs.id, lhs_bid['price'])
        }))
      else: return self.cache_it('best_syn_ask', None)
    else:
      best = None
      for s in self.lhs_switches:
        s_best_bid = s.best_bid(chain=(chain | set([self.id])), ind=ind+1)
        rhs_best_ask = s.rhs.best_ask(chain=(chain | set([self.id])), ind=ind+1)  
        if s_best_bid and rhs_best_ask:
          syn = Order({
            'book' : self.id,
            'side' : 'ask',
            'price' : rhs_best_ask['price'] - s_best_bid['price'],
            'user' : None,
            'syn' : True,
            'lhs' : (s.rhs.id, rhs_best_ask['price']),
            'op' : '-',
            'rhs' : (s.id, s_best_bid['price'])
          })
          if not best or better('bid', syn, best):
            best = syn 
      for s in self.rhs_switches:
        s_best_ask = s.best_ask(chain=(chain | set([self.id])), ind=ind+1)
        lhs_best_ask = s.lhs.best_ask(chain=(chain | set([self.id])), ind=ind+1)  
        if s_best_ask and lhs_best_ask:
          syn = Order({
            'book' : self.id,
            'side' : 'ask',
            'price' : lhs_best_ask['price'] + s_best_ask['price'],
            'user' : None,
            'syn' : True,
            'lhs' : (s.lhs.id, lhs_best_ask['price']),
            'op' : '+',
            'rhs' : (s.id, s_best_ask['price'])
          })
          if not best or better('bid', syn, best):
            best = syn
      return self.cache_it('best_syn_ask', best)
          
  def __str__(self):
    all_bids = list(self.bid)
    best_syn_bid = self.best_syn_bid()
    if best_syn_bid: all_bids += [best_syn_bid]
    all_bids = sorted(all_bids, cmp=cmp_bid) 
    all_bids.reverse()
    all_asks = list(self.ask)
    best_syn_ask = self.best_syn_ask()
    if best_syn_ask: all_asks += [best_syn_ask]
    all_asks = sorted(all_asks, cmp=cmp_ask)
    s = 'BOOK %s:\n' % self.id
    s += '----\n'
    if all_bids: s += ('\n'.join([str(o) for o in all_bids]) + '\n')
    s += '----\n'
    if all_asks: s += ('\n'.join([str(o) for o in all_asks]) + '\n')
    s += '----\n'
    return s


def cmp_bid(lhs, rhs): return cmp(rhs['price'], lhs['price'])
def cmp_ask(lhs, rhs): return cmp(lhs['price'], rhs['price'])
def best_bid(lhs, rhs):
  if not rhs: return lhs
  elif not lhs: return rhs 
  else: return sorted([lhs,rhs], cmp=cmp_bid)[0] 
def best_ask(lhs, rhs): 
  if not rhs: return lhs
  elif not lhs: return rhs 
  else: return sorted([lhs,rhs], cmp=cmp_ask)[0]

def better(side, lhs, rhs):
  if not lhs: return False
  if not rhs: return True
  if side == 'bid': return cmp_bid(lhs, rhs) < 0
  else: return cmp_ask(lhs, rhs) < 0
def cross_orders(bid, ask):
  return bid['price'] >= ask['price']
def cross_book(book):
  return (book.best_bid() and book.best_ask() and 
          cross_orders(book.best_bid(), book.best_ask())) 

books = {
  '3YR' : Book('3YR'),
  '5YR' : Book('5YR'),
  '7YR' : Book('7YR'),
  '3x5' : Book('3x5'),
  '3x7' : Book('3x7'),
  '5x7' : Book('5x7')
}      

books['3YR'].lhs_switches = [books['3x5'], books['3x7']]
books['5YR'].lhs_switches = [books['5x7']]
books['5YR'].rhs_switches = [books['3x5']]
books['7YR'].rhs_switches = [books['3x7'], books['5x7']]
(books['3x5'].lhs, books['3x5'].rhs) = (books['3YR'], books['5YR']) 
(books['3x7'].lhs, books['3x7'].rhs) = (books['3YR'], books['7YR']) 
(books['5x7'].lhs, books['5x7'].rhs) = (books['5YR'], books['7YR']) 

def dump():
  s = '\n'
  for b in books.itervalues():
    s += str(b)
  print(s + '\n')

def new_order(d):
  for b in books.itervalues():
    b.cache.clear()
  o = Order(d)
  if o['side'] == 'bid':
    books[o['book']].bid.append(o)
    books[o['book']].bid = sorted(books[o['book']].bid, cmp=cmp_bid)
  else:
    books[o['book']].ask.append(o)
    books[o['book']].ask = sorted(books[o['book']].ask, cmp=cmp_ask)
  dump()

    