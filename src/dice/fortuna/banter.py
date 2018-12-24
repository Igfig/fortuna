"""
Created on Jul 1, 2015

@author: Ira

TODO: handle data patterns too, or something like that
TODO: accept a name specified in __init__, instead of only just "fortuna"
TODO: (maybe?) recognize whether her name was said in the speaker's previous
	line, and treat that as if it was the current line.
	so if someone says "Fortuna" and then "Fuck you." she'll recognize it.  
TODO: something for "fortuna plz"
TODO: make the question pattern more versatile
"""
import json
import random
import re


class BanterController(object):
	"""
	manages all of Fortuna's configurable text responses
	i.e. not dice rolls, commands, or commentary
	
	TODO: maybe this should be rewritten to fit a parser pattern?
		Hmm, maybe not. If this successfully completes but the real parsers 
		don't, we'll get unexpected behaviour: banter, but nothing to denote
		that there was anything wrong with the dice expression.  
	"""

	def __init__(self, json_path, name="Fortuna"):
		
		with open(json_path) as jfile:
			self.exchanges = [BanterExchange(name, obj) for obj in json.load(jfile)]
	
	def handle_msg(self, msg):
		types_matched = set()
		response_lines = []
		
		for exchange in self.exchanges:
			
			# skip this exchange if it's of a type we already have a match for
			if any(t for t in exchange.types if t in types_matched):
				continue
			
			# see if we have a match
			groups = exchange.match(msg, types_matched)
			
			if not groups:
				continue
			
			# add this exchange's lines to our response
			response_lines += exchange.get_response(groups)
			types_matched.update(exchange.types)
			
			# do we need to break the sequence now
			if exchange.stop_progression:
				break
		
		return response_lines
	

class BanterExchange(object):
	"""
	A stimulus/response pair describing how Fortuna responds to specified chat 
	phrases.
	
	Instance properties that'll get added out of the json:
	id: a string to identify the triggering phrase
	patterns_text: a list of regex patterns, all of which the text of a line
		must match to trigger the response
	patterns_data: not sure how I want to do this yet, or if I want to split it
		or something, but it'll be for testing the line's metadata, eg the
		speaker. Maybe also things that are only happening in the code, like
		checking the insult_level or something like that
		might unify this with patterns_text in some way, since text and data aren't 
		passed separately any more.
	responses: a list of sequences of lines Fortuna might say in response to a 
	matching line
	types: a list of strings; no more than one exchange of each type will be matched.
	stop_progression: if this is true, no more exchanges will be matched after this.
	"""
	
	def __init__(self, name, exchange_dict):
		self.responses = {}
		self.stop_progression = False
		self.types = []
		
		# import all the json
		self.__dict__ = exchange_dict
		
		# compile all the regex patterns, to improve long-term performance.
		# also replace all "<name>" in patterns with the bot's actual name 
		# (usually Fortuna) 
		compiled_patterns = [re.compile(pattern.replace("<name>", name), re.I)
								for pattern in self.patterns_text]
		self.patterns_text = compiled_patterns
	
	def get_response(self, groups):
		"""
		Choose a response to submit. 
		"""
		response_lines = []
		
		for line in random.choice(self.responses):
			q = line.format(*groups)
			response_lines.append(q)
		
		return response_lines
	
	def match(self, msg, types_matched):
		"""
		See if the line meets this exchange's criteria.
		@return any of the matched regex groups
		"""
		line = msg.line
		groups = [line]  # because group 0 is always the full pattern
		
		for pattern in self.patterns_text:
			match = pattern.search(line)
			
			try:
				groups += match.groups()
			
			except AttributeError:
				# no match found
				return []
		
		return groups
