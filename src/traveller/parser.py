import re
import traveller
from dice.parser import BaseParser


class TravellerParser(BaseParser):
	def __init__(self, to_parse):
		self.input = to_parse
		
		if to_parse.strip()[0] == '"':
			self.result = []
			return
		
		try:
			self.result = self.parse(to_parse.strip())
			pass
		
		except:  # TODO what errors can be thrown?
			self.result = []
	
	def make_output_lines(self):
		return self.result
		
	
	@staticmethod
	def parse(to_parse):
		match = re.match("TRAVEL\s+(\w+)", to_parse)
		terrain = match.group(1)
		return traveller.travel(terrain)
