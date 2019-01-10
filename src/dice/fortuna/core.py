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

import random, traceback, sys, asyncio

from asyncio.queues import Queue
from aioconsole import ainput

from dice.parser import DiceParser
from dice.starwars.parser import StarWarsParser
from dice.fortuna.banter import BanterController
from traveller.parser import TravellerParser

PARSERS = {
	'default': DiceParser,
	'DiceParser': DiceParser,
	'starwars': StarWarsParser,
	'StarWarsParser': StarWarsParser,
	'traveller': TravellerParser
}

DEFAULT_CONFIG = {
	"BOT CONFIG": {
		"nickname": "Fortuna",
		"banter_file": "C:/xampp/htdocs/Fortuna/fortuna-master/banter.json",
		# FIXME surely we can find a better way to define the default banter file location. This one only works on my own computer.
		"parser": "default"
	}
}


class Message:
	def __init__(self, line, **kwargs):
		self.line = line
		
		for kwarg, val in kwargs.items():
			self.__dict__[kwarg] = val
	
	def __str__(self):
		return self.line


class Response(Message):
	def __init__(self, line, original, **kwargs):
		self.original = original
		
		super().__init__(line, **kwargs)


class DefaultBot:
	"""
	The default bot for if no other is provided. Just pulls continuously from
	standard in.
	"""
	# FIXME banter actions don't work correctly in this context
	
	def __init__(self, controller, config):
		self.name = config["BOT CONFIG"]["nickname"]
		
		# connect to controller
		self.queue_to_bot = controller.queue_to_bot
		self.queue_to_controller = controller.queue_to_controller
	
	async def start(self):
		await asyncio.gather(self.start_input(), self.read_queue())
	
	async def start_input(self):
		while True:
			text = await ainput("")
			msg = Message(text)
			await self.queue_to_controller.put(msg)
			# note that there's no standard interrupt or anything in this barebones version.
	
	async def read_queue(self):
		while True:
			received = await self.queue_to_bot.get()
			print(self.name + ":", received.line)


class Fortuna:
	"""
	The central controller for Fortuna. The bot, and some other components, will
	differ depending on our medium (command line, irc, web app, etc), but this
	class will always be part of the package.
	"""
	
	def __init__(self, bot_class, config=DEFAULT_CONFIG):
		# parse config
		self.bot_class = bot_class
		self.config = config
		self.name = config['BOT CONFIG']['nickname']
		banter_file = config['BOT CONFIG']['banter_file']
		self.banter = BanterController(banter_file, self.name)
		
		self.parsers = []
		config_parsers = config['BOT CONFIG']['parser']
		parser_names = set([p.strip() for p in config_parsers.split(',')])
		for pname in parser_names:
			try:
				self.parsers.append(PARSERS[pname])
			except KeyError:
				# that parser isn't in the list
				pass
		
		# create variables for queues
		self.queue_to_controller = None
		self.queue_to_bot = None
		
		asyncio.run(self.start())
		
		# XXX we may want to use threads after all, but for now let's try doing it with just async
		"""
		# make controller thread
		controller_thread = threading.Thread(target=self.start)
		controller_thread.start()
		
		# init bot and make its thread
		bot = bot_class(self, config)
		bot_thread = threading.Thread(target=bot.bot_start)
		bot_thread.start()
		"""
	
	async def start(self):
		print("Starting " + self.name)
		
		await self.init_queues()
		bot = self.bot_class(self, self.config)
		await asyncio.gather(self.run(), bot.start())
	
	async def init_queues(self):
		"""
		We don't do this inside the constructor because the queues need to be instantiated within
		the same event loop as everything else.
		"""
		# TODO we might be able to use the more in-depth async functions to add this to the event
		# loop in the constructor
		self.queue_to_controller = Queue()
		self.queue_to_bot = Queue()
	
	async def run(self):
		while True:
			msg = await self.queue_to_controller.get()
			responses = self.handle_msg(msg)
			
			for response_line in responses:
				response = Response(response_line, msg)
				await self.queue_to_bot.put(response)
	
	# XXX a little worried about how if this takes a long time, it might prevent the bot from
	# receiving messages. Maybe make this async too? hmm...
	def handle_msg(self, msg: Message):
		responses = []
		parsed = []
		exceptions = []
		
		for parser in self.parsers:
			# we want to catch and log any and all excpetions, so:
			# noinspection PyBroadException
			try:
				parsed.append(parser(msg.line))
			except Exception:
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
			output_lines = p.make_output_lines()
			
			for output in output_lines:
				try:
					# noinspection PyUnresolvedReferences
					line = msg.source + ", " + output
				except AttributeError:
					# no source or username was specified
					line = output
				
				responses.append(line)
		
		return responses


def main():
	banter_json_file = "../../../banter.json"
	
	config = {"BOT CONFIG": {
		"nickname": "Fortuna",
		"banter_file": banter_json_file,
		"parser": "default, starwars, traveller"
	}}
	
	Fortuna(DefaultBot, config)


if __name__ == "__main__":
	main()
