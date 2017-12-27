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
TODO: the code for putting parens around a roll if it's inside another dice 
	expression is really ugly; it uses isinstance(), which is bad. Can we figure 
	out another way to do it?
	Actually I think isinstance() is fine if we use an interface... does that apply 
	here?  
TODO: don't super like the output format for things like 2d(1d6)

TODO: dist situations have a problem still: the end comment needs to be put on the 
	multiroll, and the prev comments need to go on the end
	current situation: 
	1d10 hats, 2d4 socks for: bill -> [7] hats, [1, 2] socks for = 7, 3  bill
TODO: first, the comments just need to go on the outputs 
TODO: problem with parens print: 3 + (2 - 5) -> 3 + 2 - 5 = -3 = 0 
TODO: add **kwargs to each __init__() and roll() so we can ignore 
	params we don't need.

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
import random, sys, operator, traceback
from util.borrower import Borrower
from abc import ABC, abstractmethod
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

ARITHMETIC_SYMBOLS = {	'add': 		'+',
						'subtract':	'-',
						'multiply':	'*',
						'divide':	'/'}

COMPARISON_FUNCTIONS = {'<' : operator.lt,
						'<=': operator.le,
						'=' : operator.eq,
						'!=': operator.ne,
						'>=': operator.ge,
						'>' : operator.gt }

	
#===========================================================================
# HELPER FUNCTIONS
#===========================================================================


def get_value_or_attr(obj, attr_name, default, *args, **kwargs): #really needs a better name
	"""
	If obj.attr is callable, return obj.attr()
	if it isn't callable but it does exist, return obj.attr
	otherwise return default
	
	Kinda wondering if maybe I should take out the part that returns the attribute itself if it's not callable.
	Or at least have an option for that... it might be useful in some cases, but the most used case is for
	roll_if_dice().
	
	Use this version when debugging, it makes it a lot easier to find the problem 
	"""
	if hasattr(obj, attr_name):
		attr = getattr(obj, attr_name)
		
		if callable(attr):
			return attr(*args, **kwargs)
		else:
			return getattr(obj, attr_name)
		
	else:
		return default
'''
def get_value_or_attr(obj, attr_name, default, *args): #really needs a better name
	"""
	if obj.attr is callable, return obj.attr()
	if it isn't callable but it does exist, return obj.attr
	otherwise return default 
	
	Use this version in play maybe, it's technically more correct? I think?
	Although the fact that it's less debuggable seems like a problem.
	"""
	
	try:
		return getattr(obj, attr_name)(*args)
	
	except TypeError:
		#obj.attr wasn't callable
		return getattr(obj, attr_name)
	
	except AttributeError:
		#obj.attr doesn't exist
		return default
'''
	
def roll_if_dice(to_roll, *args, **kwargs):
	"""
	If it can be rolled, roll it; otherwise don't.
	Not sure if there's a better place for this. 
	Also I'm not really sure if we should be letting "roll" be an attr instead of always a method
	because if roll is a method but we get a typeError from inside it, we'll be passed the method itself
	when really, it should just straight-up crash
	can we define a new exception maybe? 
	"""
	return get_value_or_attr(to_roll, 'roll', to_roll, *args, **kwargs)


#===========================================================================
# ABSTRACT BASE CLASSES
#===========================================================================

class Rollable(ABC):
	@abstractmethod
	def roll(self):
		return

class Result(ABC):
	"""
	TODO needs more methods?
	"""
	'''
	@abstractmethod
	def __add__(self, other):
		return
	
	@abstractmethod
	def __mul__(self, other):
		return
	
	@abstractmethod
	def __sub__(self, other):
		return
	
	@abstractmethod
	def __truediv__(self, other):
		return
	
	@abstractmethod
	def __pow__(self, other):
		return
	
	@abstractmethod
	def __mod__(self, other):
		return
	
	@abstractmethod
	def __neg__(self):
		return
	
	@abstractmethod
	def __abs__(self):
		return
	
	@abstractmethod
	def total(self):
		return
	'''
	
#===========================================================================
# CLASSES
#===========================================================================

class Die(Rollable):
	"""
	a kind of die that you can roll. Subclasses for special things like FATE 
	dice, decks of cards, etc
	"""
	def __init__(self, size):
		self.lowest = 1
		#self.size = size
		
		try:
			# check if size is a zero-padded string; if so, start at 0 instead of 1
			if size.startswith('0'):
				size = size.lstrip('0')
				self.lowest = 0
		except AttributeError:
			#not a atring I guess
			pass
		
		self.size = size
		
	
	def __eq__(self, other):
		return self.size == other.size
	
	def __repr__(self):
		if isinstance(self.size, Dice) or isinstance(self.size, Roll):
			return "d(" + str(self.size) + ")"
		
		return "d" + repr(self.size)
	
	def __str__(self):
		return repr(self)
	
	def average(self):
		'''not the most efficient way to calc this perhaps, but it'll work for 
		dice with unusual sides'''
		outcomes = self.outcomes()
		return sum(outcomes) / len(outcomes)
	
	def outcomes(self):
		size = int(self.size)
		return list(range(self.lowest, self.lowest + size))
	
	def roll(self, *, status=0, **kwargs):
		"""
		@param status: see DieResult for an explanation
		"""
		return DieResult(self, status)


class DieResult(Result, int):
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

	def __new__(cls, die, status=0):
		
		try:
			# "die" is an actual Die
			die = random.choice(die.outcomes())
			
		except AttributeError:
			# "die" is just a number, so take it as-is
			die = int(die)	
			
			'''
			#think this is no longer needed	
			except TypeError:
				# "die" is actually a DiceResult or RollResult
				die = random.randint(1, int(roll_if_dice(die.size)))
			'''
			# and if it's not one of those, let the exception ride
			
		obj = int.__new__(cls, die)
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
		return repr(self)
	
	def __add__(self, other):
		return DieResult(super().__add__(other), status=0)
		#reset status to 0 to avoid the sum of [1-, 2, 4+] being printed as 6+  
	
	def __radd__(self, other):
		return self.__add__(other)
	
	def __mul__(self, other):
		if isinstance(other, (int, Die, Dice, Roll)): #FIXME: isinstance is a little dirty, is there a better way?
			return DieResult(super().__mul__(other), status=0)
		else:
			return int(self) * other


class Dice(Rollable, Borrower):
	"""
	A roll of some number of dice.
	
	@param number: the number of dice to roll
	@param die: the Die object to be rolled
	@param comment: the comment attached to the die
	@param roll_negatives: if the number param is negative, should we [True] roll
		a number of dice equal to abs(number), or [False] roll nothing?
	"""
	
	def __init__(self, number, die, comment="", roll_negatives=False):
		
		super().__init__(DiceResult) #Borrower init
		
		self.number = number
		self.comment = comment
		self.roll_negatives = roll_negatives
		
		if isinstance(die, Die):
			self.die = die
#		elif die in ('F', 'f'):
#			self.die = FateDie()
# 		elif die in ('draw', 'raw', 'deck', 'eck', 'card'):
# 			self.die = CardDeck()
# 		elif die in "BSADPCF":
# 			pass
		else:
			self.die = Die(die)
	
#	def __int__(self):
#		return self.roll()
	
	def __repr__(self):
		full_string = ""
		
		#FIXME: this is really ugly
		if isinstance(self.number, Dice) or isinstance(self.number, Roll):
			full_string += "(" + str(self.number) + ")"
		else:
			a = self.number
			full_string += str(a)
			
		if isinstance(self.die, Dice) or isinstance(self.die, Roll):	
			full_string += "(" + str(self.die) + ")"
		else:
			full_string += str(self.die)
		
		full_string += self.comment
		
		return full_string
	
	def average(self):
		return self.die.average() * self.number;
	
	def roll(self, *, sort=False, status=0):
		"""@return list of dice rolls"""
		return DiceResult(self, self.comment, sort, status)
	
	#===========================================================================
	# MATH EMULATION
	#===========================================================================
	
	def __add__(self, other):
		"""create a Roll object containing the sum of the two"""
		return Roll(self) + other
	
	def __sub__(self, other):
		return Roll(self) - other
	
	def __mul__(self, other):
		return Roll(self) * other
	
	def __truediv__(self, other):
		return Roll(self) / other
	
	def __radd__(self, other):
		return Roll(other) + self
	
	def __rsub__(self, other):
		return Roll(other) - self
	
	def __rmul__(self, other):
		return Roll(other) * self
	
	def __rtruediv__(self, other):
		return Roll(other) / self


class DiceResult(Result, list):
	# TODO: maybe we should change the iterator function for this so it only gives 
	# non-dropped dice, and then have a special iterator for getting all dice
	# including dropped ones
	# that does cause some troubles with len, and with indexing in general though...
	# maybe it's better to do it the simple way after all.
	
	def __init__(self, dice, comment="", sort=False, status=0):
		
		self.show_dice = False
		
		# get value for number of dice
		
		if hasattr(dice.number, 'roll'):
			# it's a Dice or a Roll or something
			
			self.show_dice = True
			
			# get the result we're going to use this time around
			num_roll = dice.number.roll()
			num = int(num_roll) 
			
			# define behaviour when converted to string			
			if hasattr(dice.number, 'queue') and len(dice.number.queue) > 0:
				# it's a roll with multiple terms, and needs parens around it
				self.numstr = "(" + str(num_roll) + ")"
			else:
				self.numstr = str(num_roll)
			
		else:
			# it's just an int or something
			num = dice.number
			self.numstr = repr(num) #dunno why it has to be repr and not str
		
		if dice.roll_negatives:
			num = abs(num)
		
		# get value for size of dice

		if hasattr(dice.die, 'size') and hasattr(dice.die.size, 'roll'):
			# it's a Dice or a Roll or something
			self.show_dice = True
			
			# get the result we're going to use this time around
			die_roll = roll_if_dice(dice.die.size)
			die = Die(die_roll)
			
			# define behaviour when converted to string
			if hasattr(dice.die, 'queue') and len(dice.die.queue) > 0:
				# it's a roll with multiple terms, and needs parens around it
				self.dicestr = "d(" + str(die_roll) + ")"
			else:
				self.dicestr = "d" + str(die_roll)
			
		else:
			#it's just an int or something
			die = dice.die
			self.dicestr = repr(die)
		
		# actually roll the dice!
		
		rolls = [die.roll(status=status) for _ in range(int(num))]
		
		if sort:
			rolls = sorted(rolls)
		
		super().__init__(rolls) # because this is a list subclass, after all
		
		#assign the other attributes
		
		self.comment = comment
		self.die = die
		
		self.queue = dice.queue[:]
		self.total_func = self.sum
		self.keep_sorted = sort
		
		while self.queue:
			cur_operation = self.queue.pop(0)
			cur_operation(self)
			
	
	def __iadd__(self, other):
		super().__iadd__(other)
		self.queue += other.queue #dunno if this is ideal	
		#die size and total_func of other are ignored; this might also not be ideal
		#TODO: figure that out
		
		if self.keep_sorted:
			self.sort()
		
		return self
	
	def __int__(self):
		return self.total()
	
	def __iter__(self):
		"""iterate though the dice that are still in the roll"""
		return iter([r for r in super().__iter__() if r.status>=0])
	
	def iter_all(self):
		"""iterate through all dice attached to the roll, even ones that have been dropped"""
		return super().__iter__()
	
	def __len__(self):
		"""number of dice currently in the roll"""
		return len([_ for _ in self])
	
	def len_all(self):
		"""number of dice that have ever been in the roll, even if they're now discarded"""
		return len(list(self.iter_all()))
	
	def __repr__(self):
		outstr = super().__repr__() + self.comment
		
		if self.show_dice:
			outstr = "(" + self.numstr + self.dicestr + "=)" + outstr
		
		return outstr

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
		"""as in, the most commonly-seen value"""
		#TODO this is probably biased towards high or low numbers, right?
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
		
		return list(zip(*sorted_by_mostest))[0]
	
	
	def highest(self, n=1):
		if n:
			return sorted(self)[-n:]
		else:
			return []
	
	def lowest(self, n=1):
		if n:
			return sorted(self)[:n]
		else:
			return []
		
	def single_highest(self):
		return self.highest()[0]

	def single_lowest(self):
		return self.lowest()[0]
	
	def sum(self):
		return sum(self)
	
	def total(self):
		return self.total_func()
	


class DiceInt(int, Rollable, Result):
	"""
	An int that you can use like a Dice or DiceResult object.
	So if you have a situation like 1d6 + 4, both the 1d6 and the 4
	will be of compatible types.
	"""
	
	def __new__(cls, die, comment=""):
		obj = int.__new__(cls, die)
		obj.comment = comment
		obj.number = 1
		obj.die = die
		return obj
	
	def __repr__(self):
		return super().__repr__() + self.comment
	
	def __str__(self):
		return self.__repr__()
	
	def roll(self, *args, **kwargs):
		return self
	


class Roll(Rollable, Borrower):
	"""
	@param initial: the initial Dice that is the starting point for all further manipulations 
	"""
	
	def __new__(cls, initial):
		if isinstance(initial, Roll):
			# just return that roll, instead of making a new one.
			return initial
		
		else:
			return super(Roll, cls).__new__(cls)
	
	def __init__(self, initial):
		
		if not isinstance(initial, Roll):
			super().__init__(RollResult) #Borrower init
			self.initial = initial
		
		# if initial was a Roll, then __new__ passed us that instead of a new Roll instance, 
		# and we don't need to initialize it again.
	
	
	def __add__(self, dicegroup):
		return self.add(dicegroup)
	
	def __mul__(self, dicegroup):
		return self.multiply(dicegroup)
	
	def __sub__(self, dicegroup):
		return self.subtract(dicegroup)
	
	def __truediv__(self, dicegroup):
		return self.divide(dicegroup)
	
	def __radd__(self, dicegroup):
		return Roll(dicegroup) + self
	
	def __rsub__(self, dicegroup):
		return Roll(dicegroup) - self
	
	def __rmult__(self, dicegroup):
		return Roll(dicegroup) * self
	
	def __rtruediv__(self, dicegroup):
		return Roll(dicegroup) / self
	
#	def __int__(self):
#		return int(self.roll())
	
	def __repr__(self):
		full_string = str(self.initial)
		
		for dice in self.queue:
			full_string += " " + ARITHMETIC_SYMBOLS[dice.name] + " " + str(dice.args[0]) 
		
		return full_string	 
	
	def average(self):
		#TODO check that this works
		
		total = DiceInt(self.initial.average())
		
		for mc in self.queue[:]: #using a copy of the queue just in case
			func = getattr(total, mc.name)
			dice = mc.args[0]
			total = func(dice.average())
		
		return total
	
	@property
	def number(self):
		return len(self.queue) + 1 # the +1 is for the initial value 
	
	def roll(self, sort=False):
		return RollResult(self, sort)
	

class RollResult(Result): #TODO: add some more sequence emulation methods
	
	def __init__(self, roll, sort=False):
		self.roll = roll
		self.result = [roll_if_dice(roll.initial, sort=sort)]
		self.signs = ['+']
		self.queue = roll.queue[:]	#we make this copy because we're going to destructively iterate over it
		
		while self.queue:
			self.queue.pop(0)(self)
			
	def __int__(self):
		return self.total()
	
	
	def __repr__(self):
		full_string = repr(self.result[0])
		
		for r, s in zip(self.result[1:], self.signs[1:]): #self.signs[0] is always +
			
			# FIXME: a bit ugly maybe?
			# needs to lose the results inside parens
			# 4 * (6 - 2) -> 4 * (6 - 2 = 4) = 16 
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
	
	def find_mostest(self, attr, keyfunc, n=1):
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
				#bests.sort(key=lambda x: x[0]) #i.e. sort by the keyvalue
				bests.sort(key=lambda x: keyfunc(x[0])) #i.e. sort by the keyvalue
				
				if len(bests) > n:
					bests = bests[-n:] 
				
		return bests
	
	def highest(self, n=1):
		return [key for (key, _) in self.find_mostest("highest", lambda x: x, n)]
		
	def lowest(self, n=1):
		return [key for (key, _) in self.find_mostest("lowest", lambda x: -x, n)]
	
	def single_highest(self):
		return self.highest()[0]

	def single_lowest(self):
		return self.lowest()[0]
	
	def total(self):
		"""
		total sum value of roll
		works in left-to-right order, so if you want something calculated first, put it in a subroll
		TODO: make conform to BEDMAS
		"""
		subtotal = 0;
		
		try:
			for (r, s) in zip(self.result, self.signs):
				try:
					g = r.total()
				except AttributeError:
					g = r
				#g = get_value_or_attr(r, 'total', r)
				
				op = OPERATOR_FUNCTIONS[s]
				subtotal = op(subtotal, g)
		except Exception as e:
			print(e)
			pass
		
		return subtotal



def run_test_cases():
	test_cases = [
		Dice(1, 6),
		Dice(1, 6) + 5,
		Dice(1, 6) * 3,
		Dice(1, 6) * Dice(1, 4),
		
		Dice(Dice(2,4), 6),
		Dice(Dice(2,4).roll(), 6)]
	

	for test_case in test_cases:
		result = test_case.roll()
		print(test_case, ":\t", result)


def main():
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
	
	#print(random.randint(1, Die(6).roll()))
	
	def trigger(d):
		return operator.ge(d, 4)
	
	#r = Roll(Dice(3, Die(6))).add(Dice(8, Die(12))).drop_highest(2).roll()
	#r = Dice(5, Die(6)).keep_highest(2).roll()
	q = Roll(Dice(3, Die(10))).subtract(Dice(2, Die(8)))
	#r = Roll(Dice(2, Die(4)))#.reroll(trigger))#.roll(sort=False)
	r = Dice(2, Die(4))#.reroll(trigger)#.roll(sort=False)
	s = Dice(r, r)
	#s = Dice(2, r)
	#print(s)
	
	#d = Dice(6, Die(4)).reroll(trigger)
	t = 1 - s	 
	#u = t.roll()
	#print(u)
	
	#print(DiceInt(q))
	#print(DieResult(r))
	
	q = Dice(Roll(Dice(2, Die(6))).add(1), Die(4))
	u = q.roll()
	print(u)
	
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
	
	v = Die(u)
	w = DieResult(u)
	print (w)
	
	print("============") 
	
	run_test_cases()

if __name__ == "__main__":
	main()