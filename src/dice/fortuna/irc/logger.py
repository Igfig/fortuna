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

	def __init__(self, queue_in, location="../../../../logs/"):
		self.queue_in = queue_in
		self.location = location.rstrip('/') + '/'	# make sure there's exactly one
													# trailing slash
	
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
		# TODO: maybe change the default so that it just tries to repeat 
		# everything since you logged out?
		with open(self.get_logpath(context), 'r') as logfile:
			return [line.strip() for line in 
				logfile.readlines()[-num_lines:]] 
				# yes, if you recall the chat you're in then you'll get back 
				# the RECALL command you just used. It's annoying, but if I
				# didn't do it like that then you'd lose the last line, which 
				# ISN'T expendable, when you recall from a different chat.
				# TODO I suppose I could have it give the last line or not 
				# depending on if it's the same chat...
	
	def start(self):
		while True:
			try:
				self.log(self.queue_in.get(block=False))
			except Empty:
				pass