"""
Created on Sep 5, 2016

@author: Igfig
"""
import random, dice
from dice import Die, Dice, DiceResult, Roll, RollResult, COMPARISON_FUNCTIONS
from dice.custom import CustomDie
from dice.strings import StrDieResult

class ComputerDie(CustomDie):
	
	def __init__(self):
		sides = [""] * 5 + [" COMPUTER"]
		super().__init__(sides)
		self.name = "Computer"
		
	def roll(self):
		return StrDieResult(self)
	
class ParanoiaDice(Dice):
	"""
	Roll some number of d6s and count the successes. Can accept a negative number
	for number of dice rolled; if so, roll abs(number of dice) dice, and subtract
	the number of failures from the number of successes.
	"""
	
	def __init__(self, number, comment="", **kwargs):
		super().__init__(number, Die(6), comment=comment, 
						roll_negatives=True)
	
	def roll(self, **kwargs):
		return ParanoiaDiceResult(self, self.comment, **kwargs)
	
	def __add__(self, other):
		if not isinstance(other, ParanoiaDice):
			return super().__add__(other)
		
		self.number += other.number
		self.comment += " +" + other.comment 
			# FIXME this is the wrong format for short string extension!
			# What was that article I was reading on the topic?
		return self
	
	def __sub__(self, other):
		if not isinstance(other, ParanoiaDice):
			return super().__sub__(other)
		
		self.number -= other.number
		self.comment += " -" + other.comment 
			# FIXME this is the wrong format for short string extension!
			# What was that article I was reading on the topic?
		return self


class ParanoiaDiceResult(DiceResult):
	
	def __init__(self, dice, comment, **kwargs):
		super().__init__(dice, comment)
		self._subtract_failures = dice.number < 0#dice.subtract_failures
		self.set_total_to_count(COMPARISON_FUNCTIONS[">"], 4)
		
	def total(self):
		total = super().total()
		
		if self._subtract_failures:
			num_failures = len(self) - total 
			total -= num_failures
		
		return total
		
		
class ParanoiaRoll(Roll):
	"""
	Roll some ParanoiaDice, and additionally roll a ComputerDie.
	"""
	def roll(self, **kwargs):	
		return ParanoiaRollResult(self)


class ParanoiaRollResult(RollResult):
	def __init__(self, roll, **kwargs):
		super().__init__(roll)
		self.computer = ComputerDie().roll()
	
	def __repr__(self):
		return super().__repr__() + self.computer
	
	def __str__(self):
		return super().__repr__() +  " = " + str(self.total()) \
			+ str(self.computer)

def main():
	for i in range(-5, 8):
		die  = ParanoiaDice(i, " foo")
		roll = ParanoiaRoll(die) 
		print(roll.roll())
	
	die1 = ParanoiaDice(4, " foo")
	die2 = ParanoiaDice(1, " bar")
	roll = ParanoiaRoll(die1 - die2)
	print(roll.roll())

if __name__ == "__main__":
	main()