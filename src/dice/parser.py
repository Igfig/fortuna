"""
Parses correctly formatted text strings into Roll objects

This version uses eval

TODO: variables? x := 1d4, x-1
TODO: look at roll20 again
TODO: inline dice rolls with [[...]]??
TODO: execute arbitrary python code, possibly with {{...}} 
TODO: maybe allow arbitrary named dice, like dF or dCard but for anything
TODO: actually implement dCard properly
TOOD: maybe we shouldn't get rid of parens if they're being used solely for math and not for nesting rolls
		i.e. 2 + (3 - 5) vs (2d4)d6
		Oddly we do do this for actual rolls, sorta...
		(1d4*2) - 3 -> ([1] * 2 = 2) - 3 = -1
TODO: any line starting with a number will be treated as a die roll.
	maybe have something like, if the output string would be the same as the input, don't return it?
	well no, because that'd kill 1 + 1 = 2
	see, the problem we're getting is 1 fart -> 1 fart = 1 

FIXME: 1d4#1d4 is a crash, and it has to do with  [""] * RollResult. (also one time 1d4x1d4 did something similar)
	basically it doesn't know how to multiply those together properly? It tries to cast the result as a list or whatever
	And if you do 2#whatever causes a ton of lag and sometimes just doesn't happen?
	Plus it does the {{2}} -> line before, which is really pretty unnecessary

TODO: check what intended behaviour is for #. Separate lines or same line?
	
FIXME:
	parens are messy
	Igfig	1d(4+3d2)
	Fortuna	Igfig, (1d4 + [1, 2, 2] = 9=)[8] = 8
	
	Igfig	2d2 oxen x 2d4 anuses
	Fortuna	Igfig, {{[1, 1] oxen = 2}} -> {[1, 1] anuses, [1, 1] anuses} = {2, 2}

FIXME: distrib is all jacked up still

FIXME: very large rolls (eg 1000d8) crash fortuna and she doesn't recover
	"irc.client.MessageTooLong: Messages limited to 512 bytes including CR/LF"
ah the problem is in the IRC part

FIXME: "+1d12" causes a crash
FIXME: punctuation in comment causes AttributeError
		that means we can't do decimals at all
"""


import re
from dice.rollable import Dice, DiceResult, DiceInt, Roll, RollResult, \
		OPERATOR_FUNCTIONS, COMPARISON_FUNCTIONS, roll_if_dice

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

parens_str = "\((?P<contents>[^()]*)\)"
multistr = "(?:(?P<multi>.*?)x(?=\s*(?:\d|\(|\{)))?(?P<rolls>.*)"
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
		
		if to_parse.strip()[0] == '"':
			self.result = False
			return
		
		try:
			self.result = self.parse(to_parse.strip())
			
		except NotADiceExpressionError:
			#was not an expression at all
			self.result = False
		
		
	def __str__(self):
		return "\n".join([str(ol) for ol in self.make_output_lines()])
		
		
	def make_output_lines(self):

		if not self.result:
			# probably was not actually a roll
			return []
		
		if len(self.result) == 1 and \
			self.result[0]["repetitions"] == 1 and \
			len(self.result[0]["line"]) == 1 and \
			len(self.result[0]["line"][0]["multirolls"]) == 1 and \
			self.result[0]["line"][0]["multirolls"][0]["multi"] in [None, 0, 1] and \
			len(self.result[0]["line"][0]["multirolls"][0]["rolls"][0].result) == 1 and \
			isinstance(self.result[0]["line"][0]["multirolls"][0]["rolls"][0].result[0], int):
			# was a single int
			# FIXME: can surely do better than this massive bullshit if statement
			return []
		
		output_lines = []
		
		for res in self.result:
			if int(res['repetitions']) > 1:
				output_lines.append("{{" + str(res['repetitions']) + "}} ->")
			
			for full_roll in res['line']:
				output_multi = []
				output_groups = []
				
				for multiroll in full_roll['multirolls']:
					if multiroll['multi'] != None: 	# need to specify None because 0 would eval to false
													# and in theory we might want to be able to get 0
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
							group_str += DiceParser.compile_roll_versions(og)
						
						elif isinstance(og[0], RollResult):
							group_str += "(" + DiceParser.compile_roll_versions(og) + ")"
								
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
	def compile_roll_versions(group_versions):
		"""
		FIXME: oh hmm this still isn't right. 
		2x 1-(1d6+1) -> 1 - ({[6] + 1 = 7, [3] + 1 = 4}) = {-6, -3}
		when really the two diceresults should end up together in a {} and the +1 should only happen once 
		"""
		group_str = ""
		
		if len(group_versions) > 1:
			group_str += "{"
			
		group_str += ", ".join([str(gv) for gv in group_versions]) 
		
		if len(group_versions) > 1:
			group_str += "}"
			
		return group_str
	
	@staticmethod
	def parse(to_parse):
		"""
		parse a full roll expression, such as 
		"3#1d6; 2x1d20+4 vs: a, b, c; 1d4x3d6kh2, 4dx6+2d4 damage"
		"""
		
		# deal with parens
		# we're doing this before all the 
		
		subrolls = {} # using this as a sort of weird hashtable
		subroll_index = 0;
		
		while True:
			parens = parens_pat.search(to_parse)
			
			if not parens:
				break
			
			parens_contents = parens.group('contents')
			
			subrolls[subroll_index] = DiceParser.parse_roll(parens_contents, subrolls)
			to_parse = parens_pat.sub("{" + str(subroll_index) + "}", to_parse, 1)
			subroll_index += 1
			
			
		# back to original shit
		
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
				repetitions = roll_if_dice(
									DiceParser.parse_roll(full_roll_match.group('numlines'), subrolls))
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
					'multirolls': DiceParser.parse_multiroll(
									full_roll_match.group('multis'), subrolls), 
					'comment': dist} for dist in distribs] })
			
		return full_rolls
		
	
	@staticmethod
	def parse_multiroll(to_parse, subrolls):
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
				x_roll = DiceParser.parse_roll(multimatch.group("multi"), subrolls)
				x_roll_result = roll_if_dice(x_roll)
				repetitions = int(x_roll_result)
			
			multi_roll = DiceParser.parse_roll(multimatch.group("rolls"), subrolls)
			
			all_rolls.append({ 	'multi': x_roll_result, 
								'rolls': [multi_roll.roll() for _ in range(repetitions)] })
		
		return all_rolls
		
	
	@staticmethod
	def parse_roll(to_parse, subrolls):
		"""
		parse a compound roll expression, such as "3d8kh1 + 2d6 + 5 damage"
		
		TODO: This whole function is incredibly hacky, fix it!
				specifically, this is really hacky with the indexing. 
				Maybe we should move the indexing functions to a new method, at least?
		
		TODO: should always return a Roll object
		
		@return: Roll object		
		"""
		
		'''
		q = re.sub(dice_or_int_pat, 'DiceParser.parse_dice("' + '\g<0>' + '")', to_parse)
		
		print(q)
		print(eval(q))
		return None
		
		
		'''
		dice = {}
		dice_index = ord('a');
		dice_matches = dice_or_int_pat.finditer(to_parse)
		
		for dice_match in dice_matches:
			dice[chr(dice_index)] = DiceParser._parse_dice_from_match(dice_match, subrolls)
			to_parse = dice_or_int_pat.sub("dice['" + chr(dice_index) + "']", to_parse, 1)
			dice_index += 1
		
		#convert first term into a Roll object if it isn't already
		#if dice['a'] and not isinstance(dice['a'], Roll):
		if 'a' in dice:
			dice['a'] = Roll(dice['a'])
		
		try:
			return Roll(eval(to_parse))
		
		except NameError:
			# the line includes non-parseable content, and so is probably not a dice expression
			raise NotADiceExpressionError(to_parse)
		
		except SyntaxError:
			#included parseable content but was probably not intended to be parsed
			raise NotADiceExpressionError(to_parse)
		
	
	@staticmethod
	def parse_dice(to_parse):
		"""
		parse a simple dice expression, like "2d10rl1" 
		@return Dice object 
		
		might be superfluous
		TODO: get rid of maybe?
		"""
		
		dicematch = re.match(dicepat, to_parse)
		return DiceParser._parse_dice_from_match(dicematch, {})#.roll()
		
		# TODO: need to make it so a Dice expression can take another dice-type object as an argument, in place of an int.
		# except I think we can do that to some degree already, at least? 
		
		
	@staticmethod
	def _parse_dice_from_match(dice_match, existing_rolls):
		"""
		FIXME: extremely hacky in spots
		"""
		
		dice_groups = dice_match.groupdict()
		
		for k, v in dice_groups.items():
			if k in ('count', 'countnum', 'dicenum', 'diesize', 'manipnum'): #the rest are just strings
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
		
		try:
			comment = dice_groups["comment"].rstrip()
		except:
			pass
		
		if not dice_groups["diesize"]:
			try:
				# this is just a single int, not a parsed_dice expression
				return DiceInt(dice_groups["dicenum"], comment)
			
			except TypeError:
				# is not just an int
				parsed_dice = dice_groups["dicenum"]
			
		else:
			parsed_dice = Dice(dice_groups["dicenum"], dice_groups["diesize"], comment)
		
		#j = str(parsed_dice)
		
		# parsed_dice manips
		
		if dice_groups["manip"]:
			for manipmatch in re.finditer(dice_manip_str, dice_groups["manip"]):
				manip_groups = manipmatch.groupdict()
				
				if manip_groups["explode"]:
					parsed_dice.explode()
					continue
					
				manipnum = int(manip_groups["manipnum"])
			
				if manip_groups["hold"]:
			
					hold = manip_groups["hold"]
					
					if hold == 'kh':
						parsed_dice.keep_highest(manipnum)
					elif hold == 'kl':
						parsed_dice.keep_lowest(manipnum)
					elif hold == 'dh':
						parsed_dice.drop_highest(manipnum)
					elif hold == 'dl':
						parsed_dice.drop_lowest(manipnum)
					elif hold == 'rh':
						parsed_dice.reroll_highest(manipnum)
					elif hold == 'rl':
						parsed_dice.reroll_lowest(manipnum)
			
			
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
						
						parsed_dice.explode(trigger=trigger)
					
					elif advmanip == "r":
						parsed_dice.reroll(trigger, maxdepth=1)
					
					elif advmanip == "rr":
						parsed_dice.reroll(trigger)
					
				else:
					raise ValueError("parsed_dice manip matched with unexpected value")
		
		# comparisons / counting
		
		if dice_groups["count"]:
			count = dice_groups["count"]
			countnum = int(dice_groups["countnum"])
			
			parsed_dice.set_total_to_count(COMPARISON_FUNCTIONS[count], countnum)
		
		
		if dice_groups["sort"]:
			parsed_dice.sort()
			
		return parsed_dice
	
		

class NotADiceExpressionError(Exception):
	#TODO: get it to record some context
	pass

#TODO: need more custom exceptions, and more specific.
#NotADiceExpressionError is not super clear on what it means.

def run_test_cases():
	test_cases = [
		# single dice group
		"1d6",
		"3ds8",
		"3d6kh1",
		"4d4rr<2",
		"5d3!",
		"4d4!rl2!",
		
		# arithmetic
		"2 + 3",
		"1d12 + 1",
		"2d6 + 1d10",
		
		# comments
		"2d6 + 5 slashing + 1d8 radiant + 2d6 sneak attack",
		"1d4 horses.",	#FIXME: RETURNS NULL
		
		# bedmas
		"1 + 2 * 3",
		"1d6 + 2d3 * 2d2",
		
		# parens
		"(1d4)d6",
		"2d(2d3)",
		"3 + (2 - 5)",
		"4 * (6 - 2)",
		"(1d6-1) + 1",
		"6 - (4 + (1d4*2) - 3)",
		
		# multirolls
		"2x 3d4",
		"1d4 x 2d6",
		"2d3 x 2d6",
		"(2d3)d2 x 1d8",
		"1d4, 1d6, 1d8",
		"1d3 x 3d6, 1d10",
		"1, 2d2, 1d3 x 2d6", #FIXME: bad placement of {{}}
		"2d2 x 1d4 x 2d8", #FIXME maybe? do we want to allow multiple xs?
		
		# multi-line rolls
		"2 # 2d6",
		"1d4 # 3d4",
		"2d2 # 2d8",
		"1d3 # 1d4 x 1d6", #FIXME maybe we should reroll the 1d4 here each time?
		"1d2, 1d3 # 2d8", #FIXME this doesn't work... but how would that work anyway?
		
		# distribs
		"1d10 hats, 2d4 socks for alice",
		"1d10 hats, 2d4 socks for: bill",
		"1d20+1 attack, 1d8+1 damage vs: bill, tim",
		
		# non-dice-expressions (should return empty)
		"foo",
		"foo; bar",
		"(foo, bar)",
		"('foo')",	#FIXME: returns when it shouldn't
		"foo bar",
		"foo bar?",
		"foo bar foo, bar foobar.",
		'"foo"']
	
	for test_case in test_cases:
		parser = DiceParser(test_case)
		print(test_case, ":\t", parser)
	
	#TODO: set up some test cases that should fail, 
	#	   and assert what the exceptions should be	


if __name__ == "__main__":
	
	#q = DiceParser("1d4x1d20+11 attack; 2x1d10rr<3+1d8rr<3+2d6rr<3+10, 1d4r<3+1d8r<3+2d6r<3+10 damage")
	#q = DiceParser("(1d6+1d4)d6 (fart)")
	#q = DiceParser("10+")
	#q = DiceParser("(10+)")
	#q = DiceParser("2d(1d20)+7 atk, 2x2d6+1 dmg vs: fart, poop; 1d4 foot")
	#q = DiceParser("2d(1d20 poop + 1 farts) + 7 atk")
	
	#s = "2x(1d4+1)d(1d8) + 1"
	#s = "(1d4, 2d6)d3"
	s = "1d6 fart"
	#s = "1 + (1d6-1)"
	#s = "2d2 x 1d4 - (1d6 + 1)"
	#s = "2x 1 - (1d6+1)"
	#s = "foo"
	
	q = DiceParser(s)
	print(q)
	
	print("============") 
	
	run_test_cases()
	
	
	
	
	