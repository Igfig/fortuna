"""
Created on Jul 1, 2015

@author: Ira

TODO: someday maybe have it get logged with all the html styling.
Like, instead of writing directly to a file, pipe it to logparser.
(which needs a better name)
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
		#TODO: maybe change the default so that it just tries to repeat everything since you logged out?
		#TODO: be able to request the history from a different convo, so you can ask in PMs 
		with open(self.get_logpath(context), 'r') as logfile:
			return [line.strip() for line in 
				logfile.readlines()[-num_lines-1:-1]] 
			#the -1s are so we don't recall the RECALL command 
	
	def start(self):
		while True:
			try:
				self.log(self.queue_in.get(block=False))
			except Empty:
				pass