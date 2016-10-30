"""
Created on Jun 8, 2015

@author: Ira Fich

TODO: occasionally when you roll Fortuna will give you all 1s, and then say 
	"Just kidding" and give you your real result
TODO: Fortuna keeps track of your rolls and comments on them. 
	"That's the third 20 you've rolled today. Don't worry, I'm just lulling you 
	into a false sense of security."
	"That's the third 1 you've rolled today. That's not bad luck, I just don't 
	like you."
TODO: MORE TSUNDERE
TODO: insult level
"""

import queue, random, threading, traceback, sys
from dice.parser import DiceParser
from dice.starwars.parser import StarWarsParser
from dice.fortuna.banter import BanterController

PARSERS = {	'default' :			DiceParser,
			'DiceParser' : 		DiceParser,
			'starwars' : 		StarWarsParser,
			'StarWarsParser' :	StarWarsParser }

"""
The default bot for if no other is provided. Just pulls continuously from 
standard in.
"""
class DefaultBot:
	
	def __init__(self, config, controller):
		self.name = config["BOT CONFIG"]["nickname"]
		self.queue_to_bot = controller.queue_to_bot
		self.queue_to_controller = controller.queue_to_controller
	
	def start(self):
		input_thread = threading.Thread(target=self.start_input)
		input_thread.start()
		
		while True:
			try:
				print(self.name + ":", self.queue_to_bot.get(block=False)[0])
			except queue.Empty:
				pass	
	
	def start_input(self):
		while True:
			self.queue_to_controller.put(Message(input()))
			
			
"""
The central controller for Fortuna. The bot, and some other components, will 
differ depending on our medium (command line, irc, web app, etc), but this
class will always be part of the package. 
"""
class Fortuna(object):

	def __init__(self, config, botClass=DefaultBot):
		# parse config
		self.name = config['BOT CONFIG']['nickname']
		banter_file = config['BOT CONFIG']['banter_file']
		self.banter = BanterController(banter_file, self.name)
		
		self.parsers = []
		for pname in set(
				[p.strip() for p in config['BOT CONFIG']['parser'].split(',')]):
			try:
				self.parsers.append(PARSERS[pname])
			except KeyError:
				#that parser isn't in the list
				pass
		
		# create queues
		self.queue_to_controller = queue.Queue()
		self.queue_to_bot = queue.Queue()
		
		# make controller thread
		controller_thread = threading.Thread(target=self.start)
		controller_thread.start()
		
		# init bot and make its thread
		bot = botClass(config, self)
		bot_thread = threading.Thread(target=bot.start)
		bot_thread.start()
		

	def start(self):
		print("Starting " + self.name)
		
		while True:
			msg = self.queue_to_controller.get()
					
			responses = self.handle_msg(msg)
			
			for response in responses:
				self.queue_to_bot.put((response, msg))
			
	
	"""
	@param msg: a Message object
	"""
	def handle_msg(self, msg):
		responses = []
		parsed = []
		exceptions = []
		
		for parser in self.parsers:
			try:
				parsed.append(parser(msg.line))
			except:
				exceptions.append(sys.exc_info())
			
		if exceptions and not parsed:
			# note that if we got an exception but parsers isn't empty, then
			# one of the parsers returned something successfully
			
			for exception in exceptions:
				traceback.print_exception(*exception)
			
			msg_length = random.randint(9, 12)
			return ["".join([random.choice("bfghkl") for _ in range(msg_length)])]
		
		responses += self.banter.handle_msg(msg)
		
		for p in parsed:
			q = p.make_output_lines()
			
			for output in q:
				try:
					line = msg.source + ", " + output
				except AttributeError:
					#no source or username was specified
					line = output
				
				responses.append(line)
		
		return responses
		
	

class Message(object):
	def __init__(self, line, **kwargs):
		self.line = line
		
		for kwarg, val in kwargs.items():
			self.__dict__[kwarg] = val
			
	def __str__(self):
		return self.line



def main():
	banter_json_file = "../../../banter.json"
	
	config = { "BOT CONFIG" : {
		"nickname": "Fortuna",
		"banter_file": banter_json_file,
		"parser": "default, starwars"
	}}
	
	Fortuna(config);



if __name__ == "__main__":
	main()
