"""
Created on Jul 1, 2015

@author: Ira
"""

import datetime, traceback
from queue import Empty

class Logger(object):
	"""
	formats and logs all lines from chat
	"""

	def __init__(self, queue_in, location="../../../logs/"):
		self.queue_in = queue_in
		self.location = location.rstrip('/') + "/"
	
	def get_logpath(self, channel):
		return self.location + channel.lstrip('#') + "_" + \
				str(datetime.date.today()) + ".txt"
	
	def log(self, msg):
		with open(self.get_logpath(msg.context), 'a') as logfile:
			try:
				logfile.write(str(msg) + "\n")
				
				if msg.target:
					print("[" + msg.target + "] " + str(msg))
				else:
					print(msg)
					
			except Exception as err:
				traceback.print_tb(err.__traceback__)
	
	def recall(self, context, num_lines=1):
		with open(self.get_logpath(context), 'r') as logfile:
			return [line.strip() for line in 
				logfile.readlines()[-num_lines:]]
	
	def start(self):
		while True:
			try:
				self.log(self.queue_in.get(block=False))
			except Empty:
				pass