import discord
import asyncio
import logging
import threading
import queue

from dice.fortuna import Fortuna, Message
from dice.fortuna.irc.logger import Logger

logging.basicConfig(level=logging.INFO)

client = discord.Client()

# @client.event
# async def on_ready(self):
#
# 	print('Logged in as')
# 	print(self.user.name)
# 	print(self.user.id)
# 	print('------')


class FortunaBot(discord.Client):
	
	def __init__(self, controller, config):
		super().__init__()
		
		log_path = ""    # TODO get from config
		
		# connect to controller
		self.queue_to_bot = controller.queue_to_bot
		self.queue_to_controller = controller.queue_to_controller
		
		# set up logger
		self.queue_to_logger = queue.Queue()
		self.logger = Logger(self.queue_to_logger, log_path)
		logger_thread = threading.Thread(target=self.logger.start)
		logger_thread.start()
	
	@asyncio.coroutine
	async def on_ready(self):
		print('Logged in as')
		print(self.user.name)
		print(self.user.id)
		print('------')
	
	@asyncio.coroutine
	async def on_message(self, message):
		fortuna_message = DiscordMessage(message)
		
		# self.log(fortuna_message) # TODO
		# self.handle_command(fortuna_message) # TODO
		self.queue_to_controller.put(fortuna_message)
		
		
		if message.content.startswith('!test'):
			counter = 0
			tmp = await self.send_message(message.channel, 'Calculating messages...')
			async for log in self.logs_from(message.channel, limit=100):
				if log.author == message.author:
					counter += 1
			
			await self.edit_message(tmp, 'You have {} messages.'.format(counter))
		elif message.content.startswith('!sleep'):
			await asyncio.sleep(5)
			await self.send_message(message.channel, 'Done sleeping')
	
	def bot_start(self):
		"""Start the bot."""
		
		# start reply handler
		reply_thread = threading.Thread(target=self.bot_start_reply_loop)
		reply_thread.start()
		
		# start client
		token = self.load_token("token.txt")
		self.run(token)
		
	def bot_start_reply_loop(self):
		# TODO we can probably roll this into the async loop somehow
		while True:
			self.reply_loop()
	
	async def reply_loop(self):
		try:
			line, original_msg = self.queue_to_bot.get(block=False)
			# self.send_and_log(original_msg.channel, line)
			await self.send_message(original_msg.channel, line)
		
		except queue.Empty:
			# that's fine, won't always be a message to print.
			pass
	
	async def send_and_log(self, channel, message):
		await self.send_message(channel, message)
		print(message)  # TODO
	
	@staticmethod
	def load_token(token_file_path):
		with open(token_file_path) as token_file:
			return token_file.read().strip()


class DiscordMessage(Message):
	def __init__(self, message, **kwargs):
		self.channel = message.channel
		self.author = message.author
		
		line = message.content
		
		super().__init__(line, **kwargs)


def main():
	Fortuna(FortunaBot)


if __name__ == '__main__':
	main()
