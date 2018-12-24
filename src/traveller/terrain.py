import random, math
from util.functions import cmp


class Terrain:
	def __init__(self, symbols, spread, min_density, max_density):
		self.symbols = symbols  # an iterable containing the symbols that will appear. Adjacent
								# symbols will appear together. The centermost one is where we
		# start.
		self.spread = spread    # Affects how many different symbols can show up at once. Amount
								# is spread*2 + 1
		self.min_density = min_density  # how densely the symbols are packed at minimum.
		self.max_density = max_density
	
	def get_density(self, depth):
		return self.min_density + depth * (self.max_density - self.min_density)
	
	def travel(self, length, width):
		top = len(self.symbols)
		half = math.ceil(top/2)
		current = half
		
		lines = []
		
		for step in range(length):
			# how far we are from a campsite, as a fraction of max such distance
			# i.e. 1 at midday, 0 just after leaving or before arriving
			# this influences symbol density
			depth = 1 - abs(1 - 2*step/length)
			
			# define how terrain changes this step.
			# Up or down one level each step, tending back towards the mean
			deviation = cmp(half, current)  # = 1 if below avg, -1 if above
			bias = max(0, min(current + deviation, top))
			shift_options = [
				max(current-1, 0),
				current,
				min(current+1, top),
				bias
			]
			current = random.choice(shift_options)
			
			# build one step's worth of terrain
			line = ""
			while len(line) < width:
				s_min = max(0, current - self.spread)
				s_max = min(length, current + self.spread)
				density = self.get_density(depth)
				
				if random.random() < density:
					line += random.choice(self.symbols[s_min:s_max])
				else:
					line += " "
			lines.append(line[0:width])  # trim extra characters due to long symbols
			
		return lines
