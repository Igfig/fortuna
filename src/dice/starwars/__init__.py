"""
Created on Jan 23, 2016

@author: Ira
"""

from dice.custom import CustomDie
from dice.str import * #@UnusedWildImport
import random

class StarWarsDie(CustomDie):
	sides = []
	name = ""
	
	def __init__(self):
		self.size = len(self.sides)
	
	def __eq__(self, other):
		return hasattr(other, 'sides') \
			and hasattr(other, 'name') \
			and self.sides == other.sides \
			and self.name == other.name
	
	def __lt__(self, other):
		return hasattr(other, 'name') and self.name < other.name
	
	def __hash__(self):
		return hash(self.name)
	
	def __repr__(self):
		return self.name
	
	def roll(self, status=0):
		return StarWarsDieResult(random.choice(self.sides))


class BoostDie(StarWarsDie):
	sides = [" "," ","s","sa","aa","a"]
	name = "B"
	
class SetbackDie(StarWarsDie):
	sides = [" "," ","f","f","t","t"]
	name = "S"

class AbilityDie(StarWarsDie):
	sides = [" ","s","s","ss","a","a","sa","aa"]
	name = "A"

class DifficultyDie(StarWarsDie):
	sides = [" ","f","ff","t","t","t","tt","ft"]
	name = "D"
	
class ProficiencyDie(StarWarsDie):
	sides = [" ","s","s","ss","ss","a","sa","sa","sa","aa","aa","sT"]
	name = "P"

class ChallengeDie(StarWarsDie):
	sides = [" ","f","f","ff","ff","t","t","ft","ft","tt","tt","fD"]
	name = "C"

class ForceDie(StarWarsDie):
	sides = ["d","d","d","d","d","d","dd","L","L","LL","LL","LL"]
	name = "F"


class StarWarsDieResult(StrDieResult):
	order = "sfatTDLd"
	
	def __lt__(self, other):
		return self.order.find(self) < self.order.find(other)  
	
	def __hash__(self):
		return self.order.find(self)

class StarWarsDice(StrDice):
	cancels = ("sf", "at")

if __name__ == "__main__":
	
	d = StarWarsDice(AbilityDie(), AbilityDie(), DifficultyDie(), ProficiencyDie(), ProficiencyDie())
	#d = AbilityDie()
	#print(d)
	print(d.roll())