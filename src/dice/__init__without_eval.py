"""
Created on Apr 30, 2013

@author: Ira

This is the version where when you add or drop a die to/from a roll, it
gets marked with a + or -

TODO: extension for saving a roll result, eg to draw a hand of cards or roll a 
		DiTV pool.
TODO: "roll" without replacement, e.g. drawing cards from a deck
		already have this partially in the CardDeck class, but make it generic
		by means of a NonReplacingDie class maybe
FIXME: adding a roll to itself causes an infinite loop, which is not what we want

Some notes on syntax:

2d8 + 3d6 + 4 -> [1,8] + [1,3,6] + 4 = 23
2d8, 3d6 + 4 -> [1,8], [1,3,6] + 4 = 9, 14
2d8; 3d6 -> [1,8] = 9; [1,3,6] = 10 

2 * 2d8 + 4 -> 2 * [1,8] + 4 = 22
2 x 2d8 + 4 vs bill -> {[1,8], [3,7]} + 4 = {13, 14} vs bill
2 # 2d8 + 4 vs bill -> [1,8] + 4 = 13 vs bill; [3,7] + 4 = 14 vs bill

2d8 + 4 vs: bill, bob -> [1,8] + 4 vs bill; [3,7] + 4 vs bob

kh, kl, rh, rl -> keep highest, keep lowest, remove highest, remove lowest
"""

#===========================================================================
# IMPORTS
#===========================================================================

import random, sys, operator
from igfig.borrower import Borrower
#from builtins import enumerate
#from _ctypes_test import func


#===========================================================================
# STATIC VARIABLES
#===========================================================================

OPERATOR_FUNCTIONS = {	'+': operator.add,
						'-': operator.sub,
						'*': operator.mul,
						'/': operator.truediv }
						#FIXME: operators after this point just crash us
						#'%': operator.mod,
						#'^': operator.pow }

COMPARISON_FUNCTIONS = {'<' : operator.lt,
						'<=': operator.le,
						'=' : operator.eq,
						'!=': operator.ne,
						'>=': operator.ge,
						'>' : operator.gt }

	
#===========================================================================
# HELPER FUNCTIONS
#===========================================================================

def get_value_or_attr(obj, attr, default, *args): #really needs a better name
	"""
	If obj.attr is callable, return obj.attr()
	if it isn't callable but it does exist, return obj.attr
	otherwise return default 
	"""
	
	try:
		return getattr(obj, attr)(*args)
	
	except TypeError:
		#obj.attr wasn't callable
		return getattr(obj, attr)
	
	except AttributeError:
		#obj.attr doesn't exist
		return default
	
def roll_if_dice(to_roll, *args):
	"""
	If it can be rolled, roll it; otherwise don't.
	Not sure if there's a better place for this. 
	"""
	return get_value_or_attr(to_roll, 'roll', to_roll, *args)


#===========================================================================
# CLASSES
#===========================================================================

class Die(object):
	"""
	a kind of die that you can roll. Subclasses for special things like FATE 
	dice, decks of cards, etc
	"""
	def __init__(self, size):
		self.size = int(size)
	
	def __eq__(self, other):
		return self.size == other.size
	
	def __repr__(self):
		return "d" + str(self.size)
	
	def roll(self, status=0):
		"""
		@param status: see DieResult for an explanation
		"""
		return DieResult(random.randint(1, self.size), status)


class CustomDie(Die):
	"""
	a die with custom sides
	"""
	def __init__(self, sides):
		self.sides = sides
		self.size = len(sides)
	
	def __eq__(self, other):
		return hasattr(other, 'sides') and self.sides == other.sides 
	
	def __repr__(self):
		return "d{" + ",".join([str(s) for s in self.sides]) + "}"
	
	def roll(self, status=0):
		return DieResult(random.choice(self.sides), status)


class FateDie(Die):
	"""
	a Fate die, equivalent to 1d3-2
	"""
	def __init__(self):
		self.size = 1 #this may be unnecessary
	
	def __eq__(self, other):
		return isinstance(other, FateDie)
	
	def __repr__(self):
		return "dF"
	
	def roll(self, status=0):
		return DieResult(random.randint(-1, 1), status)


class CardDeck(object):
	"""
	a 52-card deck of playing cards.
	Uses strings instead of numbers, so I don't know how well it'll work with 
	all the math.
	"""
	def __init__(self):
		names = range(2, 10) + ['J', 'Q', 'K', 'A']
		suits = ['c', 'd', 'h', 's']
		self.cards = [str(n) + s for s in suits for n in names]
		self.discard = []


class DeckDraw(Die):
	"""
	TODO: make this work with the existing system
	"""
	
	def __init__(self, deck):
		self.deck = deck
	
	def roll(self, status=0):
		try:
			x = random.choice(self.cards) #TODO: make compatible with DieResult
			
		except ValueError:
			# no cards left in the deck
			# so shuffle the discard back into the deck
			# FIXME: this will occasionally result in drawing the same card
			# twice in one multidraw
			self.cards = self.discard
			self.discard = []
			x = random.choice(self.cards)
			
		self.cards.remove(x)
		self.discard.append(x)
		return x


class DieResult(int):
	"""
	The result of the roll of a single die.
	We use this instead of a plain int because it lets us apply metadata to the roll.
	Specifically, status: whether the die has been dropped from or added to a roll
	-1 = dropped
	 0 = normal
	 1 = added 
	
	TODO: may want to have some more math functions so we don't get confused if we add
	two together
	"""
	
	def __new__(cls, val, status=0):
		obj = int.__new__(cls, val)
		obj.status = status
		return obj

	def __repr__(self):
		if self.status < 0:
			return super().__repr__() + "-"
		elif self.status > 0:
			return super().__repr__() + "+"
		else:
			return super().__repr__()
		
	def __str__(self):
		return self.__repr__()
	
	def __add__(self, other):
		return DieResult(super().__add__(other), status=0) 
		#reset status to 0 to avoid the sum of [1-, 2, 4+] being printed as 6+  
	
	def __radd__(self, other):
		return self.__add__(other)


class Dice(Borrower):
	"""
	A roll of some number of dice.
	
	@param num: the number of dice to roll
	@param die: the Die object to be rolled 
	"""
	
	def __init__(self, num, die):
		
		super().__init__(DiceResult) #Borrower init
		
		self.num = int(num)
		
		if isinstance(die, Die):
			self.die = die
		elif die in ('F', 'f'):
			self.die = FateDie()
# 		elif die in ('draw', 'raw', 'deck', 'eck', 'card'):
# 			self.die = CardDeck()
# 		elif die in "BSADPCF":
# 			pass
		else:
			self.die = Die(die)

	def __repr__(self):
		return "" + str(self.num) + str(self.die)
	
	def roll(self, sort=False, status=0):
		"""@return list of dice rolls"""
		a = DiceResult(self, sort, status)
		return a


class DiceResult(list):
	#TODO: maybe we should change the iterator function for this so it only gives 
	# non-dropped dice, and then have a special iterator for getting all dice
	# including dropped ones
	# that does cause some troubles with len, and with indexing in general though...
	# maybe it's better to do it the simple way after all.
	
	def __init__(self, dice, sort=False, status=0):
		
		rolls = [dice.die.roll(status) for _ in range(dice.num)]
		
		if sort:
			rolls = sorted(rolls)
		
		super().__init__(rolls)
		
		self.die = dice.die
		self.queue = dice.queue[:]
		self.total_func = self.sum
		self.keep_sorted = sort
		
		while self.queue:
			a = self.queue.pop(0)
			a(self)
		
		pass
	
	def __iadd__(self, other):
		super().__iadd__(other)
		self.queue += other.queue #dunno if this is ideal	
		#die size and total_func of other are ignored; this might also not be ideal
		#TODO: figure that out
		
		if self.keep_sorted:
			self.sort()
		
		return self
	
	def __iter__(self):
		"""iterate though the dice that are still in the roll"""
		#a = filter(lambda r: r.status>=0, super().__iter__(self))
		b = super().__iter__()
		a = iter([r for r in b if r.status>=0])
		return a 
	
	def iter_all(self):
		"""iterate through all dice attached to the roll, even ones that have been dropped"""
		return super().__iter__()
	
	def __len__(self):
		return len([_ for _ in self])
	
	def len_all(self):
		return len(list(self.iter_all()))

	#===========================================================================
	# SIMPLE ROLL MANIPULATION (changes results in-place)
	#===========================================================================
	
	def drop(self, func, *args):
		for die in self:
			if func(die, *args):
				die.status = -1
			
		return self
	
	def drop_highest(self, n=1):
		if n:	# if n == 0, we won't actually be dropping anything
			for die in sorted(self)[-n:]:
				die.status = -1
		return self
	
	def drop_lowest(self, n=1):
		if n:
			for die in sorted(self)[:n]:
				die.status = -1
		return self
		
	def keep(self, func, *args):
		return self.drop(lambda f, *a: not func(f, *a), *args)
	
	def keep_highest(self, n=1):
		return self.drop_lowest(len(self)-n)
	
	def keep_lowest(self, n=1):
		return self.drop_highest(len(self)-n)
	
	
	#===========================================================================
	# COMPLEX ROLL MANIPULATION
	#===========================================================================
	
	def explode(self, maxdepth=-1, trigger=None):
		"""@param trigger: the function that determines whether a die will explode."""

		if not trigger:
			trigger = lambda d: d >= self.die.size #by default, explodes on maximum result
		
		blast = len([i for i in self if trigger(i)])	#how big the explosion is
		
		if blast and maxdepth:	#maxdepth will be false when (if) we reach the maximum recursion depth
			shrapnel = Dice(blast, self.die).roll(status=1).explode(maxdepth-1, trigger)	#shrapnel is the result of an explosion
			self += shrapnel
		
		return self
	
	def reroll(self, func, maxdepth=-1):
		#FIXME: rr drops but doesn't roll new ones, r does nothing at all
		depth = maxdepth
		
		while depth:
			depth -= 1
			
			oldlen = len(self)
			self.drop(func)
			newlen = len(self)
			
			if oldlen == newlen:
				#we didn't drop anything
				break 
			
			self += Dice(oldlen-newlen, self.die).roll(status=1)
			
		return self
	
	def reroll_highest(self, n=1):
		self.drop_highest(n)
		self += Dice(n, self.die).roll(status=1)
		return self
	
	def reroll_lowest(self, n=1):
		self.drop_lowest(n)
		self += Dice(n, self.die).roll(status=1)
		return self
	
	
	#===========================================================================
	# METADATA MANIPULATION I guess?
	#===========================================================================
	
	def set_total_to_count(self, func, *args):
		"""
		Make the total() function work by counting the number of dice that meet some criteria 
		"""
		def count_x():
			return self.count_filtered(func, *args)
		
		self.total_func = count_x
		return self
	
	
	def set_total_to_sum(self):
		"""
		Make the total() function work by summing all the dice rolled
		"""
		self.total_func = self.sum
		return self
	
	
	#===========================================================================
	# ROLL INSPECTION (other data about rolls)
	#===========================================================================
	
	def count_filtered(self, func, *args):
		return len(self.filter(func, *args))
	
	def count_highest(self):
		highest = max(self)
		return self.count_filtered(operator.eq, highest)
	
	def count_lowest(self):
		lowest = min(self)
		return self.count_filtered(operator.eq, lowest)


	def mode(self):
		return max(set(self), key=self.count)
	
	def most_common(self): 	#just a convenience alias
		return self.mode()
	
	def largest_match(self):
		"""how many times the mode appears"""
		return self.count(self.mode())
	
	
	def filter(self, func, *args): #@ReservedAssignment
		"""@rtype: list"""
		return [r for r in self if r.status >= 0 and func(r, *args)]
	
	def filterfalse(self, func, *args):
		"""@rtype: list"""
		return [r for r in self if r.status >= 0 and not func(r, *args)]


	def filter_mostest(self, n, func=lambda x: x, *args):
		"""
		Returns a ranking of the elements in order of how well they maximize the return value of a function.
		@param n: extract the best n items. If n is negative, instead extract the worst -n items. 
		@rtype: list
		"""
		sorted_by_mostest = self.index_mostest(n, func, *args)
		
		return [self[i] for i in range(self.len_all()) if i in sorted_by_mostest]
	
	
	def index_mostest(self, n, func=lambda x: x, *args):
		"""
		Creates a ranking of indexes of elements by which element gets the best values from a function.
		Returns the indices, not the elements themselves.
		@param n: we'll return the best/worst n items  
		@param func: the function we want to maximize
		@param args: any additional arguments we might want to pass the function. Will be the same for each call.
		@rtype: list
		"""
		
		mostnesses = [(i, func(self[i], *args)) for i in range(self.len_all()) if self[i].status >= 0]
		sorted_by_mostest = sorted(mostnesses, key=operator.itemgetter(1))
		
		if n > 0:
			sorted_by_mostest = sorted_by_mostest[-n:]
		elif n < 0:
			sorted_by_mostest = sorted_by_mostest[:-n]
		else: #n == 0
			return []
		
		q = list(zip(*sorted_by_mostest))[0]
		
		return q
	
	
	def highest(self, n=1):
		if n:
			return sorted(self)[-n:]
			#return self.filter_mostest(n)
		else:
			return []
	
	def lowest(self, n=1):
		if n:
			return sorted(self)[:n]
			#return self.filter_mostest(-n)
		else:
			return []
		
	
	def sum(self):
		return sum(self)
	
	def total(self):
		return self.total_func()
	

class Roll(Borrower):
	"""
	@param initial: the initial Dice that is the starting point for all further manipulations 
	"""
	
	def __init__(self, initial):
		super().__init__(RollResult) #Borrower init
		
		self.initial = initial
	
	
	def roll(self, sort=False):
		return RollResult(self, sort)
	
	
	def __add__(self, dicegroup):
		return self.add(dicegroup)
	
	def __mul__(self, dicegroup):
		return self.multiply(dicegroup)
	
	def __sub__(self, dicegroup):
		return self.subtract(dicegroup)
	
	def __truediv__(self, dicegroup):
		return self.divide(dicegroup)
	
	__radd__ = __add__
	__rmul__ = __mul__
	#TODO: make __rsub__ and __rtruediv__ work
	#		and some other operators too maybe, like pow and mod
	#FIXME: rearranges to put the dice first and the numbers after, and sometimes combines numbers.
	#		e.g. 2 + 3 + 2d4rr<=2 + 1 gives [3, 1-, 3+] + 5 + 1 = 12


class RollResult(object): #TODO: add some more sequence emulation methods
	
	def __init__(self, roll, sort):
		self.roll = roll
		self.result = [roll_if_dice(roll.initial, sort)]
		self.signs = ['+']
		self.queue = roll.queue[:]	#we make this copy because we're going to destructively iterate over it
		
		while self.queue:
			self.queue.pop(0)(self)
			

	def __repr__(self):
		full_string = str(self.result[0])
		
		for r, s in zip(self.result[1:], self.signs[1:]): #self.signs[0] is always +
			
			if isinstance(r, RollResult):
				full_string += " " + s + " (" + repr(r) +")"
			else:
				full_string += " " + s + " " + repr(r)
		
		return full_string
	

	def __str__(self):
		if len(self.result) == 1:
			try:
				if len(self.result[0]) == 1:
					return self.__repr__()
				
			except TypeError:
				return self.__repr__()
		
		return self.__repr__() +  " = " + str(self.total())
	
	
	#===========================================================================
	# EMULATION METHODS
	#===========================================================================
	
	def __getitem__(self, key):
		"""just returns the sublist, not a RollResult object""" 
		return self.result[key]
	
	
	def __iadd__(self, dicegroup):
		return self.add(dicegroup)
	
	
	def __iter__(self):
		"""
		this is actually pretty bad, don't use it
		it's only here so that RollResult will be recognized as an iterable
		"""
		return iter(self.result) 
	
	
	def __len__(self):
		"""total number of dice rolled"""
		len_total = 0
		for r in self.result:
			try:
				len_total += len(r)
			except TypeError: #r doesn't have a __len__ function, probably because it's an integer
				pass 
		
		return len_total
		
	
	#===========================================================================
	# MANIPULATION METHODS - ARITHMETIC
	#===========================================================================
	
	def add(self, dicegroup):
		self.result.append(roll_if_dice(dicegroup))
		self.signs.append('+')
		return self
	
	def divide(self, dicegroup):
		self.result.append(roll_if_dice(dicegroup))
		self.signs.append('/')
		return self
	
	def divided_by(self, dicegroup): #convenience alias
		return self.divide(dicegroup)
	
	def minus(self, dicegroup): #convenience alias
		return self.subtract(dicegroup)
	
	def multiply(self, dicegroup):
		self.result.append(roll_if_dice(dicegroup))
		self.signs.append('*')
		return self
	
	def plus(self, dicegroup): #convenience alias
		return self.add(dicegroup)
	
	def subtract(self, dicegroup):
		self.result.append(roll_if_dice(dicegroup))
		self.signs.append('-')
		return self
	
	def times(self, dicegroup): #convenience alias
		return self.multiply(dicegroup)
	
	
	#===========================================================================
	# MANIPULATION METHODS - FILTERING
	#===========================================================================
	
	def drop(self, func, n=1):
		pass
	
	def drop_highest(self, n=1): #this could be more efficient
		"""find the highest die remaining in the roll and drop it, n times"""
		#TODO: unify with drop_lowest()
		for _ in range(n):
			highest = -sys.maxsize
			highest_holder = Dice(0, 0).roll() #just a dumb placeholder
			
			for r in self.result:
				if r:
					local_highest = get_value_or_attr(r, 'highest', [-sys.maxsize])[-1]
				
					if local_highest > highest:
						highest = local_highest
						highest_holder = r
			
			highest_holder.drop_highest();
		
		return self
	
	def drop_lowest(self, n=1):
		for _ in range(n):
			lowest = sys.maxsize
			lowest_holder = Dice(0, 0).roll() #just a dumb placeholder
			
			for r in self.result:
				if r:
					local_lowest = get_value_or_attr(r, 'lowest', [sys.maxsize])[0]
					
					if local_lowest < lowest:
						lowest = local_lowest
						lowest_holder = r
			
			lowest_holder.drop_lowest();
			
		return self
	
	def keep(self, func, n=1):
		#TODO: 
		pass
	"""
	def keep(self, func):
		#self.result[-1] = self.result[-1].keep(func) #maybe?
		self.result[-1] = self.filter(func)
		return self
	"""
	
	def keep_highest(self, n=1):
		#TODO:
		pass
		#return self.drop_lowest(len(self)-n)
	
	def keep_lowest(self, n=1):
		#TODO:
		pass
		return self.drop_highest(len(self)-n)

	#===========================================================================
	# MANIPULATION METHODS - OTHER
	#===========================================================================
	
	def explode(self, maxdepth=-1, trigger=None):
		for r in self.result:
			r.explode(maxdepth, trigger)
		return self
	
	#===========================================================================
	# ROLL INSPECTION (other data about rolls)
	#===========================================================================
	
	def filter(self, func, *args): #@ReservedAssignment
		"""@rtype: list"""
		return [r for r in self if func(r, *args)]
	
	def find_mostest(self, attr, key, n=1):
		"""
		find which subrolls best match a criterion. Needs a better name.
		@param attr: the thing we're comparing
		@param key: function, how we're judging how good the thing is. Higher number is always better.
		"""
		bests = [] #list of tuples: (keyvalue, holder). 
		#TODO: make this a proper sorted container, maybe using SortedContainers
		
		for r in self.result:
			if hasattr(r, attr): #if not, this is probably an integer and shouldn't be counted
				if callable(getattr(r, attr)):
					best_local_attrs = getattr(r, attr)(n)
				else:
					best_local_attrs = [getattr(r,attr)]
				
				bests += [(a, r) for a in best_local_attrs]
				bests.sort(key=lambda x: x[0]) #i.e. sort by the keyvalue
				
				if len(bests) > n:
					bests = bests[-n:] 
				
		return bests
	
	def highest(self, n=1):
		return [key for (key, _) in self.find_mostest("highest", lambda x: x, n)]
		
	def lowest(self, n=1):
		return [key for (key, _) in self.find_mostest("lowest", lambda x: -x, n)]
	
	def total(self):
		"""
		total sum value of roll
		works in left-to-right order, so if you want something calculated first, put it in a subroll
		TODO: make conform to BEDMAS
		"""
		subtotal = 0;
		
		for (r, s) in zip(self.result, self.signs):
			g = get_value_or_attr(r, 'total', r)
			op = OPERATOR_FUNCTIONS[s]
			subtotal = op(subtotal, g)
			
		return subtotal



if __name__ == "__main__":
	pass

	#d = Dice(4, 6).explode().drop_lowest()
	#r = Roll(d)
# 	s1 = Roll(Dice(2, Die(10))).plus(Dice(3, 4))
# 	r1 = s1.roll()
# 	print(r1)
# 	
# 	s2 = Roll(Dice(2, Die(6)))
# 	r2 = s2.roll()
# 	print(r2)
# 	
# 	s3 = Roll(9).plus(Dice(3, 1))#.multiply(Dice(1, 10))
# 	r3 = s3.roll()
# 	print(r3)
# 	pass
	
	def trigger(d):
		return operator.le(d, 2)
	
	#r = Roll(Dice(3, Die(6))).add(Dice(8, Die(12))).drop_highest(2).roll()
	#r = Dice(5, Die(6)).keep_highest(2).roll()
	
	
	r = Roll(Dice(2, Die(4)).reroll(trigger))#.roll(sort=False)
	s = Roll(Dice(1, Die(4)).reroll(trigger))

	#d = Dice(6, Die(4)).reroll(trigger)
	r = eval("2 + 3 + r + 1").roll()
	print(r)
	
# 	for q in r:
# 		print(q, end=" ")
# 	print("")
	
	#print(r.index_mostest(len(r)+1))
	#print("count min", r.count_lowest())
	
	#print(r.largest_match())
	
	#r.subtract(s)
	#r = Roll(d).add(Dice(2, Die(10))).add(Dice(3, Die(8)))
	#r.add(Roll(Dice(1, Die(8))))
	#r = Roll(d).explode().drop_highest()
	#r = Roll(d).add(Dice(2, Die(10))).drop_lowest(1)
	#x = r.roll()
	#x = RollResult(r)
	#print(*x.result)
	#print(x)
	#print(x.highest(3))
	#print(x.drop_lowest(3))