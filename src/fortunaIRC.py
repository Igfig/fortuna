'''
Created on Jun 5, 2015

@author: Ira Fich

fortuna as an IRC bot

TODO: handle nicknaming, nickname conflicts
TODO: config
	bot name, host, channels
	GM list, list of other bots/helpers 
	default sort mode, visibility for dropped/added dice
'''

import irc.bot, queue, random, threading, copy, re, configparser
import fortuna, irclogger
from queue import Empty
from dice.parser import DiceParser
from dice.starwars.parser import StarWarsParser

PARSERS = {	'default':	DiceParser,
			'starwars':	StarWarsParser }

class FortunaBot(irc.bot.SingleServerIRCBot):
	'''
	The part of Fortuna that interacts with IRC
	'''

	def __init__(self, channels, nickname, server, port, password, queue_controller_to_bot, queue_bot_to_controller, queue_bot_to_logger):
		irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], 
					nickname, #TODO: might modify this?
					 nickname)
		self.start_channels = channels
		self.password = password
		self.queue_controller_to_bot = queue_controller_to_bot
		self.queue_bot_to_controller = queue_bot_to_controller
		self.queue_bot_to_logger = queue_bot_to_logger
	
	
	def create_reply(self, line, original_msg):
		words = line.split()
		command = words[0].lower()
		text = " ".join(words[1:])
		source = original_msg.source
		extra_kwargs = {}
		
		if original_msg.is_channel():
			target = original_msg.target
		
		elif original_msg.is_global():
			target = ""
			
		else:
			# was a private message...assume it was for us or we wouldn't have seen it
			target = original_msg.source
		
		if command == "action":
			line = text
			
		elif command == "kick":
			extra_kwargs["tokick"] = original_msg.source
			line = "kicked " + source + ": " + text
			
		else:
			command = "privmsg"
			#and line stays as is
			
		#TODO return the right kind of message
		return IRCMessage(self._nickname, target, command, line, **extra_kwargs)
		
		
		
		
		
		'''
		if command not in irc.events.protocol:
			#we're being told to do a command that isn't really a valid command
			return
		'''
		
		
	
	def log(self, msg):
		if msg.target:
			self.queue_bot_to_logger.put(msg)
		
		else:
			for channel_name, channel in self.channels.items():
				if msg.source in channel.users() or (hasattr(msg, 'fakesource') and msg.fakesource in channel.users()): 
					# 'fakesource' is forsituations where msg.source would not be an accurate representation of the speaker's identity
					# e.g. if the speaker's nick changes, so the old nick that's in source doesn't describe them any more
					msg = IRCMessage.from_message(msg, target=channel_name)
					self.queue_bot_to_logger.put(msg)
		
	def on_action(self, connection, event):
		msg = IRCMessage.from_event(event)
		self.log(msg)
		self.queue_bot_to_controller.put(msg)
	
	def on_join(self, connection, event):
		msg = IRCMessage.from_event(event)
		if msg.source != self._nickname:
			#don't need to record own joining
			msg.line += "joined."
			self.log(msg)
	
	def on_nick(self, connection, event):
		msg = IRCMessage.from_event(event, target=None, line="is now known as " + event.target + ".", fakesource=event.target)
		#treat as if they're named their new name, because the channel doesn't have anybody in it with the old name
		self.log(msg)
		
	def on_nicknameinuse(self, connection, event):
		connection.nick(connection.get_nickname() + str(random.randrange(10000))) 
		# this is a pretty bad idea if you expect more than 
		# a thousand or so users at a time, so
		# TODO: make better
	
	def on_notice(self, connection, event):
		msg = IRCMessage.from_event(event)
		self.log(msg)
		#you're not supposed to reply to notices, see
	
	def on_privmsg(self, connection, event):
		msg = IRCMessage.from_event(event)
		self.log(msg)
		self.queue_bot_to_controller.put(IRCMessage.from_event(event))
		#self.log(event.source.nick, event.target, "(PRIVMSG) " + out_str, event.type) #change this probably to go to its own file
	
	def on_part(self, connection, event):
		msg = IRCMessage.from_event(event)
		if msg.line:
			msg.line = "left: " + msg.line
		else:
			msg.line = "left."
		self.log(msg)
		
	def on_pubmsg(self, connection, event):
		msg = IRCMessage.from_event(event)
		self.log(msg)
		self.queue_bot_to_controller.put(IRCMessage.from_event(event))
		#self.log(event.source.nick, event.target, out_str, event.type)
	
	def on_quit(self, connection, event):
		msg = IRCMessage.from_event(event)
		if msg.line:
			msg.line = "quit: " + msg.line
		else:
			msg.line = "quit."
		self.log(msg)
		
	def on_welcome(self, connection, event):
		for channel in self.start_channels:
			connection.join(channel)
			print('Connected to ' + channel)
	
	
	def send_and_log(self, msg):
		if msg.command == "action":
			self.connection.action(msg.target, msg.line)
		
		elif msg.command == "kick":
			if msg.is_channel():
				self.connection.kick(msg.target, msg.tokick, msg.line)
			else:
				for channel in self.channels:
					self.connection.kick(channel, msg.tokick, msg.line)
		
		else:
			self.connection.privmsg(msg.target, msg.line)
			
		self.log(msg)
	
	
	def start(self):
		"""Start the bot."""
		self._connect()
		self.connection.pass_(self.password) #TODO: extract to config
		
		while True:
			self.main_loop()
	
	
	def main_loop(self, timeout=0.2):
		self.reactor.process_once(timeout)
		
		try:
			line, original_msg = self.queue_controller_to_bot.get(block=False)
			reply = self.create_reply(line, original_msg)
			if reply:
				self.send_and_log(reply)
			
		except Empty:
			pass
		


class IRCMessage(fortuna.Message):
	
	colorcode_pat = re.compile("\x1f|\x02|\x12|\x0f|\x16|\x03(?:\d{1,2}(?:,\d{1,2})?)?", re.UNICODE)
	
	def __init__(self, source, target, command, line, **kwargs):
		self.source = source
		self.target = target
		self.command = command
		
		if self.is_channel():
			self.context = target
		else:
			self.context = "pm"
		
		super().__init__(line, **kwargs)
		
	
	def __str__(self):
		if self.is_spoken():
			#return "[" +  self.target + "] " + self.source + ": " + self.line
			return self.source + ": " + self.line
		else: 
			#return "[" +  self.target + "] " + self.source + " " + self.line
			return self.source + " " + self.line
	
	@classmethod
	def from_event(cls, event, **kwargs):
		
		source = kwargs.pop('source', event.source.nick)
		target = kwargs.pop('target', event.target)
		command = kwargs.pop('command', event.type)
		line = IRCMessage.colorcode_pat.sub("", kwargs.pop('line', " | ".join(event.arguments)))
		
		msg = cls(source, target, command, line, **kwargs)
		return msg
	
	@classmethod
	def from_message(cls, msg, **kwargs): #TODO: remake as instance method?
		newmsg = copy.copy(msg)
		
		for kwarg, val in kwargs.items():
			newmsg.__dict__[kwarg] = val
		
		return newmsg
	
	def is_global(self):
		return self.target == None
	
	def is_channel(self):
		return irc.client.is_channel(self.target)
	
	def is_spoken(self):
		return self.command in ("pubmsg", "privmsg", "pubnotice", "privnotice")
	
	
	'''
	@classmethod
	def create_reply(cls, msg, line, command):
		if msg.is_public():
			return cls(bot, msg.target, "pubmsg", line)
		
		if msg.command == "privmsg":
			return cls(bot, msg.source, "privmsg", line)
	'''
	
def set_default_config():
	config = configparser.ConfigParser()
	config['BOT CONFIG'] = {'channels': "#pwot_dnd, #pwot_dnd2",
							'nickname': "Fortuna",
							'server':	"irc.nj.us.mibbit.net",
							'banter_path': "banter.json",
							'port':		"6667",
							'parser':	"default",
							'password': "borkle"} #TODO: don't just make our password public, dude
	
	config['LOGGER CONFIG'] = {	'gms': "Igfig",
								'bots': config['BOT CONFIG']['Nickname']}
	
	with open("config.ini", 'w') as configfile:
		config.write(configfile)

def main():
	config = configparser.ConfigParser()
	config.read('config.ini')
	
	channels = config['BOT CONFIG']['channels'].split(',')
	nickname = config['BOT CONFIG']['nickname']
	server = config['BOT CONFIG']['server']
	banter_json_path = config['BOT CONFIG']['banter_path']
	port = int(config['BOT CONFIG']['port'])
	parser = PARSERS.get(config['BOT CONFIG']['parser'], 'default');
	password = config['BOT CONFIG']['password']
	
	parsers = []
	for pname in set(config['BOT CONFIG']['parser'].split(',')):
		try:
			parsers.append(PARSERS[pname])
		except KeyError:
			#that parser isn't in the list
			pass
		
	
	queue_bot_to_controller = queue.Queue()
	queue_controller_to_bot = queue.Queue()
	queue_bot_to_logger = queue.Queue()
	
	bot = FortunaBot(channels, nickname, server, port, password,
					queue_controller_to_bot, queue_bot_to_controller, 
					queue_bot_to_logger)
	controller = fortuna.Fortuna(queue_bot_to_controller, 
					queue_controller_to_bot, parsers, banter_json_path, 
					nickname)
	logger = irclogger.Logger(queue_bot_to_logger)
	
	bot_thread = threading.Thread(target=bot.start)
	controller_thread = threading.Thread(target=controller.start)
	logger_thread = threading.Thread(target=logger.start)
	
	bot_thread.start()
	controller_thread.start()
	logger_thread.start()



if __name__ == "__main__":
	main()