import discord
import asyncio
import logging

from .. import Fortuna, Message, Response, DefaultBot  # FIXME why can't I import from dice.fortuna??
# from dice.fortuna.irc.logger import Logger

logging.basicConfig(level=logging.INFO)


class DiscordMessage(Message):
	def __init__(self, message, line="", **kwargs):
		
		self.channel = message.channel
		self.author = message.author
			
		super().__init__(line, **kwargs)
	
	def __str__(self):
		to_print = [self.author.display_name, ": ", self.line]
		try:
			to_print = ["[#", self.channel.name, "] "] + to_print
		except AttributeError:
			pass
		
		return "".join(to_print)
	
	@classmethod
	def from_response(cls, response: Response):
		return cls(response.original, response.line)
	
	@classmethod
	def from_discord(cls, message):
		return cls(message, message.content)
	

class FortunaBot(discord.Client, DefaultBot):
	
	def __init__(self, controller, config):
		discord.Client.__init__(self)
		DefaultBot.__init__(self, controller, config)
		
		# set up logger
	
		# log_path = ""    # TODO get from config
		# self.queue_to_logger = asyncio.Queue()
		# self.logger = Logger(self.queue_to_logger, log_path)
	
	async def on_ready(self):
		print('Logged in as', self.user.name, f'({self.user.id})')
		print('------')
	
	async def on_message(self, message):
		message_received = DiscordMessage.from_discord(message)
		
		await asyncio.gather(
			self.log(message_received),
			self.handle_command(message_received),
			self.queue_to_controller.put(message_received))
	
	async def start(self):
		"""Start the bot."""
		
		# login
		token = self.load_token("token.txt")
		await self.login(token)
		
		# run the various loops
		await asyncio.gather(self.connect(), self.read_queue())
	
	async def read_queue(self):
		while True:
			response = await self.queue_to_bot.get()
			await self.send_and_log(response)
			
	async def send_and_log(self, response: Response):
		message = DiscordMessage.from_response(response)
		await self.log(message)
		x = await message.channel.send(message.line)
		return x
	
	async def log(self, message):
		# TODO hook this up to an actual logger
		print(message)
		
	async def handle_command(self, message):
		# TODO handle commands that are specific to discord
		pass
	
	@staticmethod
	def load_token(token_file_path):
		with open(token_file_path) as token_file:
			return token_file.read().strip()


def main():
	Fortuna(FortunaBot)


if __name__ == '__main__':
	main()
