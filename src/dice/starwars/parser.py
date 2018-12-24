"""
Created on Jan 24, 2016

@author: Ira

this is still suuuper sketchy
TODO: d100s as well
"""

from dice.parser import *  # @UnusedWildImport
from dice.starwars.rollable import BoostDie, SetbackDie, AbilityDie, \
		DifficultyDie, ProficiencyDie, ChallengeDie, ForceDie, StarWarsDice


rollstr = "ROLL\s+([BSADPCF]+)(.*)" 

DICE_NAMES = {  # TODO: construct this automatically from the names defined in each die
	"B": BoostDie,
	"S": SetbackDie,
	"A": AbilityDie,
	"D": DifficultyDie,
	"P": ProficiencyDie,
	"C": ChallengeDie,
	"F": ForceDie}


class StarWarsParser(DiceParser):

	def make_output_lines(self):
		if self.result:
			return [self.result]
		else:
			return []

	@staticmethod
	def parse(to_parse):
		dicematch = re.match(rollstr, to_parse)
		
		if dicematch:
			dice = [DICE_NAMES[r]() for r in dicematch.group(1)]
			return str(StarWarsDice(*dice).roll()) + str(dicematch.group(2)) 
		else:
			return ""


if __name__ == '__main__':
	q = StarWarsParser("ROLL AAPBDD")
	print(q)