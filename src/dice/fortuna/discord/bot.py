import threading
from asyncore import loop

import discord
import asyncio
import logging
import queue

from dice.fortuna import Fortuna, Message
from dice.fortuna.irc.logger import Logger

logging.basicConfig(level=logging.INFO)

# @client.event
# async def on_ready(self):
#
# 	print('Logged in as')
# 	print(self.user.name)
# 	print(self.user.id)
# 	print('------')

#client = discord.Client()


class FortunaBot:
	
	def __init__(self, controller, config):
		# self.loop = asyncio.get_event_loop()
		
		super().__init__()
		
		log_path = ""    # TODO get from config
		
		# connect to controller
		self.queue_to_bot = controller.queue_to_bot
		self.queue_to_controller = controller.queue_to_controller
		
		# set up logger
		self.queue_to_logger = asyncio.Queue()
		self.logger = Logger(self.queue_to_logger, log_path)
		
		client = discord.Client()
		self.client = client
		
		@client.event
		async def on_ready():
			print('Logged in as')
			print(client.user.name)
			print(client.user.id)
			print('------')
		
		@client.event
		async def on_message(message):
			fortuna_message = DiscordMessage(message)
			print(fortuna_message)
			
			# self.log(fortuna_message) # TODO
			# self.handle_command(fortuna_message) # TODO
			self.queue_to_controller.put(fortuna_message)
		
	
	# @client.event
	# async def on_ready(self):
	# 	print('Logged in as')
	# 	print(self.client.user.name)
	# 	print(self.client.user.id)
	# 	print('------')
	#
	# @client.event
	# async def on_message(self, message):
	# 	fortuna_message = DiscordMessage(message)
	# 	print(fortuna_message)
	#
	# 	# self.log(fortuna_message) # TODO
	# 	# self.handle_command(fortuna_message) # TODO
	# 	self.queue_to_controller.put(fortuna_message)
	
	# def run(self):
	# 	# start client
	#
	
	def fart(*args):
		def q(*args2):
			print('pre')
			print(args)
			print(args2)
			# f(self)
			print("post")
		return q
	
	@fart
	async def poop(self):
		print('poop')
	
	def bot_start(self):
		"""Start the bot."""
		
		
		while True:
			try:
				line, original_msg = self.queue_to_bot.get(block=False)
				await self.send_and_log(original_msg.channel, line)
			# await self.send_message(original_msg.channel, line)
			except queue.Empty:
				# that's fine, won't always be a message to print.
				pass
		
		
		# response_thread = threading.Thread(target=self.response)
		# response_thread.start()
		#
		# client_thread = threading.Thread(target=self.run)
		# client_thread.start()
		
	def run(self):
		token = self.load_token("token.txt")
		self.client.run(token)
		
		# client_loop = asyncio.new_event_loop()
		# asyncio.set_event_loop(client_loop)
		# task = client_loop.create_task(self.client.run(token))
		# client_loop.run_until_complete(task)
		
	def response(self):
		response_loop = asyncio.new_event_loop()
		asyncio.set_event_loop(response_loop)
		task = response_loop.create_task(self.main_loop())
		try:
			response_loop.run_until_complete(task)
		except:
			pass
	
	async def main_loop(self):
		# try:
		# 	self.loop.run_until_complete(self.start(*args, **kwargs))
		# except KeyboardInterrupt:
		# 	self.loop.run_until_complete(self.logout())
		# 	pending = asyncio.Task.all_tasks(loop=self.loop)
		# 	gathered = asyncio.gather(*pending, loop=self.loop)
		# 	try:
		# 		gathered.cancel()
		# 		self.loop.run_until_complete(gathered)
		#
		# 		# we want to retrieve any exceptions to make sure that
		# 		# they don't nag us about it being un-retrieved.
		# 		gathered.exception()
		# 	except:
		# 		pass
		# finally:
		# 	self.loop.close()
		
		token = self.load_token("token.txt")
		self.client.login(token)
		
		
		while True:
			try:
				line, original_msg = self.queue_to_bot.get(block=False)
				await self.send_and_log(original_msg.channel, line)
				# await self.send_message(original_msg.channel, line)
			except queue.Empty:
				# that's fine, won't always be a message to print.
				pass
	
	async def send_and_log(self, channel, message):
		x = await self.client.send_message(channel, message)
		print("a", message, x)  # TODO
		return x
	
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

	def __str__(self):
		to_print = [self.author.display_name, ": ", self.line]
		if not self.channel.is_private:
			to_print = ["[#", self.channel.name, "] "] + to_print
		
		return "".join(to_print)


def main():
	Fortuna(FortunaBot)


if __name__ == '__main__':
	main()
