"""
Parses corrctly formatted text strings into Roll objects

TODO: variables? x := 1d4, x-1
TODO: look at roll20 again
TODO: inline dice rolls with [[...]]??
TODO: execute arbitrary python code, possibly with {{...}} 
TODO: maybe allow arbitrary named dice, like dF or dCard but for anything
TODO: actually implement dCard properly
TODO: parens work, but the rolls inside the parens don't get shown in the output anywhere	
	have a thing that tells you what you rolled in a parens expression
		e.g. (1d8)d10 gets (1d8=5)[4, 4, 5, 7, 10]
	you know, maybe parens should just group arthmetic, and we should use, like, braces 
		to nest rolls?) ...ehh
TODO: nested parens do not work
TODO: possible problem with spaces in parens?
FIXME: STILL has a mysterious, hard-to-replicate problem with parens
	ah, here's one point of failure: "(10+)" is a crash
	also, commas
	basically, any symbol that has a special meaning 
TODO: maybe move comments from multirolls to single rolls? 
"""


import re, itertools
from dice import Dice, DiceResult, Roll, OPERATOR_FUNCTIONS, COMPARISON_FUNCTIONS

#===========================================================================
# REGEX PATTERNS
#===========================================================================

numstr = "\(.+?\)|\d+"
dice_manip_str = "(?:(?P<hold>kh|kl|dh|dl|rh|rl)|(?P<advmanip>!!|r|rr)" + \
					"(?P<advcond><|<=|!=|>=|>)?)(?P<manipnum>" + numstr + ")|(?P<explode>!)"
dicestr = "\s*(?P<dicenum>" + numstr + ")\s*(?:d(?P<sort>s)?\s*(?P<diesize>" + numstr + \
			"|[Ff])\s*" + "(?P<manip>(?:" + dice_manip_str + ")*)" + \
			"\s*(?:(?P<count><|<=|=|!=|>=|>)(?P<countnum>" + numstr + "))?" + ")?"
dicestr_without_groups = re.sub("P<\w*?>", ":", dicestr)
rollstr_basic = "(?:" + dicestr_without_groups + "\s*[+\*-/^%]\s*)*"  \
	+ dicestr_without_groups #+ "(?P<subcomment>[^:]*)"
rollstr_x = "(" + rollstr_basic + "\s*x\s*)?" + "(" + rollstr_basic + ")"
rollstr_x_without_groups = "(?:" + rollstr_basic + "\s*x\s*)?" + rollstr_basic
rollstr_comma = "(?:" + rollstr_x_without_groups + "\s*,\s*)*" + rollstr_x_without_groups
rollstr =  "(?:(?P<numlines>" + rollstr_basic + ")\s*#)?" + \
					"(?P<multis>" + rollstr_comma + ")(?:(?P<distrib>.*?):)?" + "(?P<comment>.*)"
			#TODO: make the rollstr_basic into a rollstr_comma
			#I guess if we have a multiroll in that section the result 
			#will get split within the same line
			#as well as over multiple lines
			#maybe that's overdoing it though

dicepat = re.compile(dicestr)
multipat = re.compile(rollstr_x)
full_rollpat = re.compile(rollstr)


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
			if res['repetitions']:
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
		
		for full_roll in full_roll_strings:
			
			rollmatch = re.match(full_rollpat, full_roll)
			
			if not rollmatch:
				continue
			
			if re.fullmatch("\d+", rollmatch.group('multis').strip()):
				#the match was just a single number, which doesn't need rolling
				continue
			
			comments = []
			repetitions_result = None
			repetitions = 1
			
			if rollmatch.group('numlines'):
				# roll once for all targets 
				# if you want to do separate, use x instead of #
				repetitions_result = DiceParser.parse_roll(rollmatch.group('numlines')).roll()
				repetitions = repetitions_result.total()
				
			
			if rollmatch.group('distrib'):	#note that this group isn't trapped inside dicestr 
									#because we used dicestr_without_groups 
				# we have a colon distribution situation
				# ie. 2d6 vs: bill, bob, george
				
				targets = [[rollmatch.group('distrib') + t] * repetitions \
						for t in rollmatch.group('comment').split(",")]
				comments = list(itertools.chain.from_iterable(targets))
			
			else:
				comments = [rollmatch.group('comment')] 
			
			full_rolls.append({ 'repetitions': repetitions_result, 
								'line': [{	'multirolls': DiceParser.parse_multiroll(rollmatch.group('multis')), 
											'comment': comment} for comment in comments] })
		
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
			multimatch = re.match(multipat, multi_string)
			x_roll_result = None
			repetitions = 1
			
			if multimatch.group(1):
				#we do in fact have a roll x roll situation, so do the first one  
				x_roll = DiceParser.parse_roll(multimatch.group(1))
				x_roll_result = x_roll.roll()
				repetitions = x_roll_result.total()
			
			multi_roll = DiceParser.parse_roll(multimatch.group(2))
			
			all_rolls.append({ 	'multi': x_roll_result, 
								'rolls': [multi_roll.roll() for _ in range(repetitions)] })
		
		return all_rolls
		
	
	@staticmethod
	def parse_roll(to_parse):
		"""
		parse a compound roll expression, such as "3d8kh1 + 2d6 + 5 damage"
		
		Note that arithmetic is done in left-to-right order, not BEDMAS. To
		change evaluation order you'll need to use parens.
		TODO: make parens actually work like this 
		
		@return: Roll object
		"""
		
		#handle parens
		while '(' in to_parse:
			parens_contents = re.search("\\(([^(]*?)\\)", to_parse).group(1)
			parens_match = re.match(rollstr_basic, parens_contents) 
			
			if parens_match:
				#replace the parens expression with the sum of the roll it describes
				to_parse = re.sub("\\(([^(]*?)\\)", DiceParser._parse_and_total_rollmatch, to_parse, count=1)
				
			else:
				#the parens weren't actually part of a dice expression 
				raise NotADiceExpressionError(to_parse)

			#TODO: actually display the parens rolls somewhere
				
		#parse it properly now that there are no parens to deal with
		return DiceParser._parse_roll_without_parens(to_parse)
	
	
	@staticmethod
	def _parse_and_total_rollmatch(match):
		return str(DiceParser._parse_roll_without_parens(match.group(1)).roll().total())		
	
	
	@staticmethod
	def _parse_roll_without_parens(to_parse):
		operator_pat = '[' + re.sub('-|\^|]', "\\\\\g<0>", ''.join(list(OPERATOR_FUNCTIONS))) + ']'
		
		dice_strings = re.split(operator_pat, to_parse)
		dice_operators = re.findall(operator_pat, to_parse)
		dice_objects = [DiceParser.parse_dice(d) for d in dice_strings]
			
		roll = Roll(dice_objects[0])
		
		for obj, oper in zip(dice_objects[1:], dice_operators):
			OPERATOR_FUNCTIONS[oper](roll, obj)
		
		return roll
	
	
	@staticmethod
	def parse_dice(to_parse):
		"""
		parse a simple dice expression, like "2d10rl1" 
		@return Dice object 
		"""
		
		dicematch = re.match(dicepat, to_parse)
		#dice_groups = [dicematch.group().strip()]
		dice_groups = dicematch.groupdict()
		"""
		try:
			dice_groups = dicematch.groupdict()
		except:
			pass
		"""
		"""
		#handle parens
		
		#for dice_group in dicematch.groups():
		for dice_group_name, dice_group in dice_groups.items():
			
			if dice_group and re.match("\\(.+\\)", dice_group):
				dice_group_contents = dice_group[1:-1]
				
				if re.match(rollstr_basic, dice_group_contents):
					#replace the dice group with the result of the dice group
					#TODO: find somewhere to display the parens roll
					total = DiceParser.parse_roll(dice_group_contents).roll().total()
					dice_groups[dice_group_name] = total
					
				else:
					#the parens weren't actually part of a dice expression 
					raise NotADiceExpressionError(dice_group_contents)
		"""
		
		#some prelims
		
		if not dice_groups["diesize"]:
			# this is just a single int, not a dice roll
			return int(dice_groups["dicenum"])
		
		else:
			dice = Dice(int(dice_groups["dicenum"]), dice_groups["diesize"])
		
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

class NotADiceExpressionError(Exception):
	#TODO: get it to record some context
	pass

if __name__ == "__main__":
	#q = DiceParser.parse_dice("4dx6rl1>2")
	#q = DiceParser.parse_roll("4dx6rl1 * 2d8+5")
	#q = DiceParser.parse_roll("1d4")
	#print(q.roll())
	#print(q.roll())
	
	#q = DiceParser.parse_multiroll("1d4 x 2d8+5")
	#q = DiceParser.parse_multiroll("2x4dx6rl1*2d8+5")
	#print(q)
	
	#q = DiceParser("1d3+1# 2d2x 4dx6rl1*2d8+5 vs: butt, fart; 2x 1d20+2, 3d8")
	#q = DiceParser("2d4x 1d20+2, 1d2x 3d8, 2+3x 2d3, 2x 1d12 fart")
	#q = DiceParser("2d4x 2d20+2, 1d2x 3d8 fart")
	#q = DiceParser("2d8+5 vs: butt, fart")
	#q = DiceParser("1d20+5 damage")
	#p = q.roll()
	#print(p, p.total())
	#q = DiceParser("3x1d20+5 atk; 4d6 damage")
	#q = DiceParser("1d3 + 1d4 * 5")
	#q = DiceParser("(1dt4d")
	
	#q = DiceParser("6ds4rr3")
	#q = DiceParser("1d4x1d20+11 attack; 2x1d10rr<3+1d8rr<3+2d6rr<3+10, 1d4r<3+1d8r<3+2d6r<3+10 damage")
	#q = DiceParser("(1d6+1d4)d6 (fart)")
	#q = DiceParser("1 foot")
	#q = DiceParser("10+")
	#q = DiceParser("(10+)")
	q = DiceParser("20#1d20+7,1d20+4")
	q = DiceParser("2#1d20+7 atk vs, 2d6 dmg vs: fart, poop")
	
	print(q)
	
	pass
	#for r in q.result[0][1]:
	#	print(r)
	
	
	
	
	