"""
Created on Sep 5, 2016

@author: Igfig
"""
import re
from dice.paranoia.rollable import ComputerDie
from dice import Roll
from dice.parser import DiceParser, numstr


dice_pat = re.compile("(?P<dicenum>\d+)d(?P<diesize>6?)")

class ParanoiaParser(DiceParser):
	
	def parse(self):
		pass