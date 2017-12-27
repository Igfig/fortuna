"""
Created on Jan 23, 2016

@author: Ira

Classes for working with dice that have strings on their faces 
instead of ints.
"""

import random
from dice.rollable import Borrower, Dice, DiceResult 
from collections import Counter

class StrDieResult(str):
	"""
	Result of a roll of a die whose sides contain strings.
	"""
	
	def __new__(cls, die, status=0):
		val = random.choice(die.sides)
		obj = str.__new__(cls, val)
		obj.status = status
		return obj
	
# 	def __repr__(self):
# 		return super().__repr__()

	def __add__(self, other):
		return StrDieResult(super(str).__add__(other), status=0)
		
		
class StrDice(Dice):
	"""
	A roll of some number of dice with sides containing strings.
	Dice need not be all the same die.
	
	@param die: the Die object to be rolled 
	"""
	cancels = []
	
	def __init__(self, *pool):
		super(Borrower).__init__(StrDiceResult) #Borrower init
		self.pool = pool
	
	def __repr__(self):
		return str(self.pool)
	
	def roll(self, status=0):
		return StrDiceResult(self, status)



class StrDiceResult(DiceResult):
	"""
	no sort param because this should always be sorted I think
	"""
	
	def __init__(self, dice, status=0):
		self.rolls = [die.roll() for die in dice.pool]
		self.result = Counter(self.rolls)
		
		for can in dice.cancels:
			smallest = min(can, key=lambda x:self.result[x])
			smallest_amount = self.result[smallest]
			
			for c in can:
				self.result[c] -= smallest_amount
		
		
	def __str__(self):
		#TODO: fix print order
		out = "[" + ", ".join(self.rolls) + "] = "
		
		for roll, num in sorted(self.result.items()):
			out += roll * num 
		
		return out

if __name__ == '__main__':
	pass