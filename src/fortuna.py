'''
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
TODO: commands, like NOTE and RECALL (records last 10 lines and sends in a PM)
'''

import queue, random, threading, traceback
from dice.parser import DiceParser
#from dice.starwars.parser import StarWarsParser
from banter import BanterController

class Fortuna(object):

	def __init__(self, queue_in, queue_out, parsers, banter_json_path, name="Fortuna"):
		self.name = name
		self.queue_in = queue_in
		self.queue_out = queue_out
		self.parsers = parsers
		self.banter = BanterController(banter_json_path, name)
	
	
	def start(self):
		print("Starting " + self.name)
		
		while True:
			msg = self.queue_in.get()
					
			responses = self.handle_msg(msg)
			
			for response in responses:
				self.queue_out.put((response, msg))
			

	def handle_msg(self, msg):
		
		responses = []
		try:
			parsed = self.parsers[0](msg.line) #TODO: very placeholdery! Need to actually send to all parsers, not just first 
			
		except Exception:
			traceback.print_exc()
			responses.append("".join([random.choice("bfghkl") for _ in range(random.randint(9, 12))]))
			
		
		else:
			for output in parsed.make_output_lines():
				try:
					line = msg.source + ", " + output
				except AttributeError:
					#no source or username was specified
					line = output
				
				responses.append(line)
			
		responses += self.banter.handle_msg(msg)
		
		return responses
	

class Message(object):
	def __init__(self, line, **kwargs):
		self.line = line
		
		for kwarg, val in kwargs.items():
			self.__dict__[kwarg] = val
			
	def __str__(self):
		return self.line


def get_input_for(input_queue):
	def get_input():
		while True:
			input_queue.put(Message(input()))
			
	return get_input

def main():
	banter_json_path = "banter.json"
	
	queue_to_controller = queue.Queue()
	queue_from_controller = queue.Queue()
	
	controller = Fortuna(queue_to_controller, queue_from_controller, DiceParser, banter_json_path)
	#controller = Fortuna(queue_to_controller, queue_from_controller, StarWarsParser, banter_json_path)
	
	bot_thread = threading.Thread(target=get_input_for(queue_to_controller))
	controller_thread = threading.Thread(target=controller.start)
	
	bot_thread.start()
	controller_thread.start()
	
	while True:
		print(queue_from_controller.get()[0])
		



if __name__ == "__main__":
	main()
