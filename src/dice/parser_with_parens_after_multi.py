"""
Parses correctly formatted text strings into Roll objects

This version uses eval

TODO: variables? x := 1d4, x-1
TODO: look at roll20 again
TODO: inline dice rolls with [[...]]??
TODO: execute arbitrary python code, possibly with {{...}} 
TODO: maybe allow arbitrary named dice, like dF or dCard but for anything
TODO: actually implement dCard properly
TODO: possible problem with spaces in parens?
FIXME: STILL has a mysterious, hard-to-replicate problem with parens
	ah, here's one point of failure: "(10+)" is a crash
	also, commas
	basically, any symbol that has a special meaning 
TODO: permit commas in distrib? Would have us start again on a new set of lines I guess.
"""


import re
from dice import Die, Dice, DiceResult, DiceInt, Roll, OPERATOR_FUNCTIONS, COMPARISON_FUNCTIONS,\
	roll_if_dice

#===========================================================================
# REGEX PATTERNS
#===========================================================================

operators = "+\*-/^%"
comparators = "<|<=|!=|>=|>"
signifiers = ",;:{}\(\)"
bracestr = "{([\w[\]]*)}"
numstr = "{[\w[\]]*}|\d+"

dice_manip_str = "(?:(?P<hold>kh|kl|dh|dl|rh|rl)|(?P<advmanip>!!|r|rr)" + \
					"(?P<advcond>" + comparators + ")?)(?P<manipnum>" + numstr + \
					")|(?P<explode>!)"
commentstr = "(?P<comment>[^" + operators + signifiers + "]*)"
					
dicestr = "\s*(?P<dicenum>" + numstr + ")(?:d(?P<sort>s)?(?P<diesize>" + \
			numstr + "|[Ff])" + "(?P<manip>(?:" + dice_manip_str + ")*)" + \
			"(?:(?P<count>" + comparators + ")(?P<countnum>" + numstr + \
			"))?)"
dicestr_without_groups = re.sub("P<\w*?>", ":", dicestr)

parens_str = "\((?P<contents>[^" + signifiers + "]*)\)"
multistr = "(?:(?P<multi>.*?)x(?=\s*(?:\d|\()))?(?P<rolls>.*)"
fullstr = "(?:(?P<numlines>[^#]+)\s*#)?(?P<multis>[^#:]+)(?::(?P<distrib>.*))?"

bracepat = re.compile(bracestr)
dice_or_int_pat = re.compile(dicestr + "?" + commentstr) #i.e. everything but the first number is optional
dicepat = re.compile(dicestr + commentstr)
dicepat_without_groups = re.compile(dicestr_without_groups)
parens_pat = re.compile(parens_str)
multipat = re.compile(multistr)
full_pat = re.compile(fullstr)

dicepat_group_names = re.findall("(?<=P<).*?(?=>)", dicestr) 

#===========================================================================
# DICE EXPRESSION PARSER 
#===========================================================================

class DiceParser(object):
	
	def __init__(self, to_parse):
		self.input = to_parse
		try:
			self.result = self.parse(to_parse)
			
		except NotADiceExpressionError:
			#was not an expression at all
			self.result = False
		
		
	def __str__(self):
		return "\n".join([str(ol) for ol in self.make_output_lines()])
		
		
	def make_output_lines(self):

		if not self.result:
			#probably was not actually a roll
			return []
		
		output_lines = []
		
		for res in self.result:
			if int(res['repetitions']) > 1:
				output_lines.append("{{" + str(res['repetitions']) + "}} ->")
			
			for full_roll in res['line']:
				output_multi = []
				output_groups = []
				
				for multiroll in full_roll['multirolls']:
					if multiroll['multi'] != None: #WHY IS THE != NONE NECESSARY THIS IS RIDICULOUS
						output_multi.append(multiroll['multi'])
						
					output_groups.append(multiroll['rolls'])
				
				
				# format the string for the multirolls, if there were any 			
				
				multi_str = ""
				
				for om in output_multi:
					strom = str(om)
					
					if '=' not in strom:
						# it's just a single number, so take off the brackets if it has any, 
						# or clear it if it doesn't
						strom = strom[1:-1]
					
					if strom:
						# if not, then we were dealing with a flat int that doesn't need to be declared
						multi_str += "{{" + strom + "}} "
				
				if multi_str:
					multi_str += "-> "
				
				
				# format the string for the groups 
				
				groups_str = ""
				group_strs = []
				
				for output_group in output_groups:
					
					first_sign = True
					group_str = ""
					
					for sign, og in zip(output_group[0].signs, zip(*output_group)):
						
						if first_sign:
							first_sign = False	#we skip the first sign because it's always +
						else:
							group_str += " " + sign + " "
						
						if isinstance(og[0], DiceResult):
							if len(og) > 1:
								group_str += "{"
								
							group_str += ", ".join([str(o) for o in og]) 
							
							if len(og) > 1:
								group_str += "}"
						
						else:
							#it's just an int
							group_str += str(og[0])
							
					group_strs.append(group_str)
				
				groups_str = ", ".join(group_strs)
				
				
				# format the string for the total
				
				totals = []
				
				for group in output_groups:
					total = ""
					if len(group) > 1:
						total += "{"
					
					total += ", ".join([str(g.total()) for g in group]) 

					if len(group) > 1:
						total += "}"
						
					totals.append(total)
				
				totals_str = ", ".join(totals)
				
				
				# assemble final output string
				
				output_str = multi_str + groups_str + " = " + totals_str + " " + full_roll['comment']
				output_lines.append(output_str)
		
		return output_lines
	
	
	@staticmethod
	def parse(to_parse):
		"""
		parse a full roll expression, such as 
		"3#1d6; 2x1d20+4 vs: a, b, c; 1d4x3d6kh2, 4dx6+2d4 damage"
		"""
		full_roll_strings = to_parse.split(';')
		full_rolls = []
		
		for full_roll_string in full_roll_strings:

			full_roll_match = full_pat.match(full_roll_string)
			
			if not full_roll_match:
				continue
			
			if re.fullmatch("\d+", full_roll_match.group('multis').strip()):
				#the match was just a single number, which doesn't need rolling
				continue
			
			if full_roll_match.group('numlines'):
				# roll once for all targets 
				# if you want to do separate, use x instead of #
				repetitions = roll_if_dice(DiceParser.parse_roll(full_roll_match.group('numlines')))
			else:
				repetitions = 1
			
			if full_roll_match.group('distrib'):
				# a colon distribution situation
				# ie. 2d6 vs: bill, bob, george
				distribs = full_roll_match.group('distrib').split(",") * int(repetitions)
			else:
				distribs = [""] * int(repetitions)
			
			#FIXME: we don't actually do the repetitions
			
			full_rolls.append({	'repetitions': repetitions, 'line': [{	
					'multirolls': DiceParser.parse_multiroll(full_roll_match.group('multis')), 
					'comment': dist} for dist in distribs] })
		
		return full_rolls
		
	
	@staticmethod
	def parse_multiroll(to_parse):
		"""
		parse a multi_string expression, such as "2x 3d6 + 3, 4d10rl1 + 4"
		
		@return list in the form [(x_roll_result, [results, of, actual, rolls]), ...] 
		"""
		
		multi_strings = to_parse.split(',')
		
		all_rolls = []
		
		for multi_string in multi_strings:
			multimatch = multipat.match(multi_string)
			x_roll_result = None
			repetitions = 1
			
			if multimatch.group("multi"):
				#we do in fact have a roll x roll situation, so do the first one  
				x_roll = DiceParser.parse_roll(multimatch.group("multi"))
				x_roll_result = x_roll.roll()
				repetitions = x_roll_result.total()
			
			multi_roll = DiceParser.parse_roll(multimatch.group("rolls"))
			
			all_rolls.append({ 	'multi': x_roll_result, 
								'rolls': [multi_roll.roll() for _ in range(repetitions)] })
		
		return all_rolls
		
	
	@staticmethod
	def parse_roll(to_parse):
		"""
		parse a compound roll expression, such as "3d8kh1 + 2d6 + 5 damage"
		
		TODO: This whole function is incredibly hacky, fix it!
		
		@return: Roll object
		"""
		
		subrolls = {} #using this as a sort of weird hashtable
		subroll_index = 0;
		
		while True:
			parens = parens_pat.search(to_parse)
			
			if not parens:
				break
			
			parens_contents = parens.group('contents')
			
			subrolls[subroll_index] = DiceParser._parse_roll_without_parens(parens_contents, subrolls)
			to_parse = parens_pat.sub("{" + str(subroll_index) + "}", to_parse, 1)
			subroll_index += 1
		
		return DiceParser._parse_roll_without_parens(to_parse, subrolls)
		
	
	@staticmethod
	def _parse_roll_without_parens(to_parse, subrolls):
		"""
		
		
		this is really hacky with the indexing. Maybe we should move the indexing functions to a new method, 
		at least?
		"""
		dice = {}
		dice_index = ord('a');
		dice_matches = dicepat.finditer(to_parse)
		
		for dice_match in dice_matches:
			dice[chr(dice_index)] = DiceParser._parse_dice_from_match(dice_match, subrolls)
			to_parse = dicepat.sub("dice['" + chr(dice_index) + "']", to_parse, 1)
			dice_index += 1
		
		try:
			return eval(to_parse)
		
		except NameError:
			# the line includes non-parseable content, and so is probably not a dice expression
			raise NotADiceExpressionError(to_parse)
			
	
	
	@staticmethod
	def parse_dice(to_parse):
		"""
		parse a simple dice expression, like "2d10rl1" 
		@return Dice object 
		
		might be superfluous
		"""
		
		dicematch = re.match(dicepat, to_parse)
		DiceParser._parse_dice_from_match(dicematch)
		
		
	@staticmethod
	def _parse_dice_from_match(dice_match, existing_rolls):
		"""
		FIXME: extremely hacky in spots
		"""
		
		dice_groups = dice_match.groupdict()
		
		for k, v in dice_groups.items():
			try:
				#if it has a parens expression marked
				dice_groups[k] = bracepat.sub("existing_rolls[\\1]", v)
			except TypeError:
				pass
			
			try:
				#if it's anything that's not just a string 
				dice_groups[k] = eval(dice_groups[k])
			except:
				pass
			
		# some prelims
		
		comment = dice_groups["comment"].rstrip()
		
		if not dice_groups["diesize"]:
			try:
				# this is just a single int, not a dice expression
				return DiceInt(dice_groups["dicenum"], comment)
			except TypeError:
				# is not just an int
				pass
			
		else:
			dice = Dice(dice_groups["dicenum"], dice_groups["diesize"], comment)
		
		# dice manips
		
		if dice_groups["manip"]:
			for manipmatch in re.finditer(dice_manip_str, dice_groups["manip"]):
				manip_groups = manipmatch.groupdict()
				
				if manip_groups["explode"]:
					dice.explode()
					continue
					
				manipnum = int(manip_groups["manipnum"])
			
				if manip_groups["hold"]:
			
					hold = manip_groups["hold"]
					
					if hold == 'kh':
						dice.keep_highest(manipnum)
					elif hold == 'kl':
						dice.keep_lowest(manipnum)
					elif hold == 'dh':
						dice.drop_highest(manipnum)
					elif hold == 'dl':
						dice.drop_lowest(manipnum)
					elif hold == 'rh':
						dice.reroll_highest(manipnum)
					elif hold == 'rl':
						dice.reroll_lowest(manipnum)
			
			
				elif dice_groups["advmanip"]:
					advmanip = manip_groups["advmanip"]
					advcond = manip_groups["advcond"]
					if advcond:
						advfunc = COMPARISON_FUNCTIONS[advcond]
					else:
						advfunc = COMPARISON_FUNCTIONS['=']
					
					def trigger(d):
							return advfunc(d, manipnum)
					
					if advmanip == "!!":
						#advanced explode 
						#def explode_trigger(d):
						#	return advfunc(d, manipnum)
						
						dice.explode(trigger=trigger)
					
					elif advmanip == "r":
						dice.reroll(trigger, maxdepth=1)
					
					elif advmanip == "rr":
						dice.reroll(trigger)
					
				else:
					raise ValueError("dice manip matched with unexpected value")
		
		# comparisons / counting
		
		if dice_groups["count"]:
			count = dice_groups["count"]
			countnum = int(dice_groups["countnum"])
			
			dice.set_total_to_count(COMPARISON_FUNCTIONS[count], countnum)
		
		
		if dice_groups["sort"]:
			dice.sort()
			
		return dice
	
	"""
	@staticmethod
	def _parse_dice_from_match(dice_match):
		dice_groups = dice_match.groupdict()
		
		print("DICE", dice_groups)
		
		#some prelims
		
		comment = dice_groups["comment"].rstrip()
		
		if not dice_groups["diesize"]:
			# this is just a single int, not a dice roll	
			return DiceInt(dice_groups["dicenum"], comment)
		
		else:
			dice = Dice(int(dice_groups["dicenum"]), dice_groups["diesize"], comment)
		
		# dice manips
		
		if dice_groups["manip"]:
			for manipmatch in re.finditer(dice_manip_str, dice_groups["manip"]):
				manip_groups = manipmatch.groupdict()
				
				if manip_groups["explode"]:
					dice.explode()
					continue
					
				manipnum = int(manip_groups["manipnum"])
			
				if manip_groups["hold"]:
			
					hold = manip_groups["hold"]
					
					if hold == 'kh':
						dice.keep_highest(manipnum)
					elif hold == 'kl':
						dice.keep_lowest(manipnum)
					elif hold == 'dh':
						dice.drop_highest(manipnum)
					elif hold == 'dl':
						dice.drop_lowest(manipnum)
					elif hold == 'rh':
						dice.reroll_highest(manipnum)
					elif hold == 'rl':
						dice.reroll_lowest(manipnum)
			
			
				elif dice_groups["advmanip"]:
					advmanip = manip_groups["advmanip"]
					advcond = manip_groups["advcond"]
					if advcond:
						advfunc = COMPARISON_FUNCTIONS[advcond]
					else:
						advfunc = COMPARISON_FUNCTIONS['=']
					
					def trigger(d):
							return advfunc(d, manipnum)
					
					if advmanip == "!!":
						#advanced explode 
						#def explode_trigger(d):
						#	return advfunc(d, manipnum)
						
						dice.explode(trigger=trigger)
					
					elif advmanip == "r":
						dice.reroll(trigger, maxdepth=1)
					
					elif advmanip == "rr":
						dice.reroll(trigger)
					
				else:
					raise ValueError("dice manip matched with unexpected value")
		
		# comparisons / counting
		
		if dice_groups["count"]:
			count = dice_groups["count"]
			countnum = int(dice_groups["countnum"])
			
			dice.set_total_to_count(COMPARISON_FUNCTIONS[count], countnum)
		
		
		if dice_groups["sort"]:
			dice.sort()
			
		return dice
	"""
	
		

class NotADiceExpressionError(Exception):
	#TODO: get it to record some context
	pass


if __name__ == "__main__":
	
	#q = DiceParser("6ds4rr3")
	#q = DiceParser("1d4x1d20+11 attack; 2x1d10rr<3+1d8rr<3+2d6rr<3+10, 1d4r<3+1d8r<3+2d6r<3+10 damage")
	#q = DiceParser("(1d6+1d4)d6 (fart)")
	#q = DiceParser("1 foot")
	#q = DiceParser("10+")
	#q = DiceParser("(10+)")
	#q = DiceParser("2d(1d20)+7 atk, 2x2d6+1 dmg vs: fart, poop; 1d4 foot")
	#q = DiceParser("2d(1d20 poop + 1 farts) + 7 atk")
	#q = DiceParser("2d4x(1d4+1)d(1d8) + 1")
	q = "(1d4, 2d6)d3"
	
	print(DiceParser(q).make_output_lines())
	
	pass
	#for r in q.result[0][1]:
	#	print(r)
	
	
	
	
	