"""
Created on Jun 5, 2015

@author: Ira Fich

fortuna as an IRC bot

TODO: handle nicknaming, nickname conflicts
	if name is registered, correct password is supplied, and nobody else is
	using the name, use it. Otherwise don't. 
TODO: more config
	default sort mode, visibility for dropped/added dice
"""

import irc.bot, irc.client
import queue, random, threading, copy, re, configparser, os
import dice.starwars
from dice.fortuna import Message, Fortuna
from dice.fortuna.irc.logger import Logger


PARSERS = {	'default':	dice.parser.DiceParser,
			'starwars':	dice.starwars.parser.StarWarsParser }

COMMAND_PAT = re.compile("(?P<command>[A-Z_]+)\s+(?P<text>.*)")

class FortunaBot(irc.bot.SingleServerIRCBot):
	"""
	The part of Fortuna that interacts with IRC
	"""

	def __init__(self, config, controller):
		logpath = config['BOT CONFIG']['log_path']
		port = int(config['BOT CONFIG']['port'])
		server = config['BOT CONFIG']['server']
		nickname = config['BOT CONFIG']['nickname']
		
		irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], 
					nickname, #TODO: might modify this?
					 nickname)
		
		#these have to come after the bot is initialized
		self.password = config['BOT CONFIG']['password']
		self.notepath = config['BOT CONFIG']['note_file']
		self.channels = config['BOT CONFIG']['channels'].split(',')
		
		self.queue_to_bot = controller.queue_to_bot
		self.queue_to_controller = controller.queue_to_controller
		
		# set up logger
		self.queue_to_logger = queue.Queue()
		self.logger = Logger(self.queue_to_logger, logpath)
		logger_thread = threading.Thread(target=self.logger.start)
		logger_thread.start()
	
	
	"""
	Turns a line to be said into an actual sendable message.
	
	@param param: an IRCMessage that needs to be responded to
	@param line: A line that will be the content of the reply message
	@return: an IRCMessage containing the line and pointed at the right context 
	"""
	def create_reply(self, original_msg, line):
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
		
		"""
		if command not in irc.events.protocol:
			#we're being told to do a command that isn't really a valid command
			return
		"""
	
	
	"""
	@return: list of strings to send 
	"""
	def get_command_lines(self, msg):
		match = COMMAND_PAT.match(msg.line)
			
		if not match:
			return []
		
		args = msg.line.split()
		command = args[0]
		
		if command == "NOTE":
			with open(self.notepath, "a") as notefile:
				notefile.write("\n" + match.group("text"))
				return ["Noted."]
			
		elif command == "RECALL":
			# some defaults
			num_lines = () # the empty tuple is part of something clever.
			context = msg.context
			
			try:
				num_lines = (int(args[1]),) # clever thing, cont.: okay so now
											# we have a 1-element tuple, right?
				context = args[2]
			except ValueError:
				# args was not parseable as an int
				return ["Usage: RECALL [number of lines] [chat name]"]
			except IndexError:
				# didn't specify all arguments, use defaults. No big deal.
				pass
				
			return self.logger.recall(context, *num_lines); # boom, payoff!
			# See, the * unpacks the tuple that is num_lines, right?
			# An empty tuple unpacked is nothing, not even None.
			# recall(context, *()) is identical to recall(context)
			# so we can use recall()'s own default values 
			# instead of specifying one ourselves 
		
		return []
		
	"""
	@param msg: a Message object
	@return: the string that Fortuna needs to say.
	"""
	def handle_command(self, msg):
		for line in self.get_command_lines(msg):
			reply = self.create_reply(msg, line)
			self.send_and_log(reply)

	
	def log(self, msg):
		if msg.target:
			self.queue_to_logger.put(msg)
		
		else:
			for channel_name, channel in self.channels.items():
				if msg.source in channel.users() or (hasattr(msg, 'fakesource') 
						and msg.fakesource in channel.users()): 
					# 'fakesource' is forsituations where msg.source would not 
					# be an accurate representation of the speaker's identity
					# e.g. if the speaker's nick changes, so the old nick that's 
					# in source doesn't describe them any more
					msg = msg.copy_with_kwargs(target=channel_name)
					#msg = IRCMessage.from_message(msg, target=channel_name)
					self.queue_to_logger.put(msg)
		
	def on_action(self, connection, event):
		msg = IRCMessage.from_event(event)
		self.log(msg)
		self.queue_to_controller.put(msg)
	
	def on_join(self, connection, event):
		msg = IRCMessage.from_event(event)
		if msg.source != self._nickname:
			#FIXME: this might not work if she's using an alternate nick
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
		self.handle_command(msg)
		self.queue_to_controller.put(msg)
	
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
		self.handle_command(msg)
		self.queue_to_controller.put(msg)
	
	def on_quit(self, connection, event):
		msg = IRCMessage.from_event(event)
		if msg.line:
			msg.line = "quit: " + msg.line
		else:
			msg.line = "quit."
		self.log(msg)
		
	def on_welcome(self, connection, event):
		for channel in self.channels:
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
		self.connection.pass_(self.password)
		
		while True:
			self.main_loop()
	
	
	def main_loop(self, timeout=0.2):
		try:
			self.reactor.process_once(timeout)
		except:
			#no big deal really, just not fully initialized yet
			pass
		
		try:
			line, original_msg = self.queue_to_bot.get(block=False)
			reply = self.create_reply(original_msg, line)
			if reply:
				self.send_and_log(reply)
			
		except queue.Empty:
			#that's fine, qon't always be a message to print.
			pass


class IRCMessage(Message):
	
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
	
	def copy_with_kwargs(self, **kwargs):
		newmsg = copy.copy(self)
		
		for kwarg, val in kwargs.items():
			newmsg.__dict__[kwarg] = val
		
		return newmsg
	
	@classmethod
	def from_event(cls, event, **kwargs):
		
		source = kwargs.pop('source', event.source.nick)
		target = kwargs.pop('target', event.target)
		command = kwargs.pop('command', event.type)
		line = IRCMessage.colorcode_pat.sub("", kwargs.pop('line', " | ".join(event.arguments)))
		
		msg = cls(source, target, command, line, **kwargs)
		return msg
	
	def is_global(self):
		return self.target == None
	
	def is_channel(self):
		return irc.client.is_channel(self.target)
	
	def is_spoken(self):
		return self.command in ("pubmsg", "privmsg", "pubnotice", "privnotice")
	
	
def set_default_config():
	#TODO do we even really need this function
	config = configparser.ConfigParser()
	config['BOT CONFIG'] = {'channels': "#pwot_dnd, #pwot_dnd2",
							'nickname': "Fortuna",
							'server':	"irc.nj.us.mibbit.net",
							'banter_file': "banter.json",
							'note_file': "notes.txt",
							'log_path': "logs/",
							'port':		"6667",
							'parser':	"default",
							'password': "borkle"} 
							#TODO: don't just make our password public, dude
	
	config['LOGGER CONFIG'] = {	'gms': "Igfig",
								'bots': config['BOT CONFIG']['Nickname']}
	
	with open("../../../../config.ini", 'w') as configfile:
		config.write(configfile)
		# FIXME change all the paths to be relative to the location of the config 
		# file, not this folder
		# or rather, we want to be able to input the paths that way, and have it 
		# automatically change them internally as needed
		

def main():
	config = configparser.ConfigParser()
	config.read('../../../../config.ini')
	
	for path in ("banter_file", "note_file", "log_path"):
		location = config['BOT CONFIG'][path]
		
		if not os.path.isabs(location):
			config['BOT CONFIG'][path] = "../../../../" + location.lstrip('/')
	
	Fortuna(config, FortunaBot)
	

if __name__ == "__main__":
	main()