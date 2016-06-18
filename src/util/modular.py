"""
Created on Dec 1, 2014

@author: Ira Fich
"""


import random
from igfig.containers import WeightedList


class Replacer():
	"""
	A class that replaces itself with a subclass of itself when you instantiate it
	"""
	subclass_weight = 0
	
	def __new__(cls, *args, **kwargs):
		subs = WeightedList(cls.__subclasses__(), [sub.subclass_weight for sub in cls.__subclasses__()])
		
		if subs and cls.go_deeper(subs):  
			newcls = subs.random_choice()
			return newcls.__new__(newcls, *args, **kwargs)
		
		#TODO: check for valid_endpoint()
		return super().__new__(cls)
	
	
	@classmethod
	def go_deeper(cls, *args, **kwargs):
		"""
		should we go deeper or not when we're given the option?
		
		You probably want to override this. For example:
		return random.randint(0, len(args[0]))
		
		and usually you'll check cls.valid_endpoint() too
		"""
		return True
	
	
	@classmethod
	def valid_endpoint(cls):
		"""
		is this class a valid point to end our search on?
		
		Probably want to override this too, as we may in the future
		want to be able to end on non-leaf nodes
		
		May want to combine this with go_deeper in some way, eventually
		"""
		return cls.__subclasses__() == []
	
	
	@classmethod
	def get_all_subclasses(cls, filterfn=lambda x:x):
		subs = []
		subs_stack = [cls]
		
		while subs_stack:
			current = subs_stack.pop(0)
			subs_stack += current.__subclasses__()
			
			if filterfn(current):
				subs.append(current)
	
		return subs
	
	
	@classmethod
	def count_subclass_weights(top_class):
		"""
		call this after you create all the classes in question, but before you create any instances of them
		usually this means put all your related Replacer subclasses in one file, and call this at the end of the file  
		"""
		
		for cls in reversed(top_class.get_all_subclasses()):
			cls.subclass_weight = 0 #reset everything in case we've called this function before
			
			if cls.valid_endpoint():
				cls.subclass_weight += 1
			for subclass in cls.__subclasses__():
				cls.subclass_weight += subclass.subclass_weight
				
		return {cls: cls.subclass_weight for cls in top_class.get_all_subclasses()}
		



class UniqueReplacer(Replacer):
	"""
	variant of Replacer that doesn't permit the same subclass to be selected more than once in a given context
	"""
	pass


class TentativeAssignment(object): #TODO: Rename?
	"""
	tentative assignment of keys to values in a constraint-satisfaction problem.
	
	Currently it's basically a holder for a DFS "string", with the ability to lock in values (with various degrees of lockedness?)
	Later, might get a more treelike structure of dependencies to reduce backtracking.
	
	Question: aren't there already constraint-satisfaction modules that might do what I want more effectively?
	They might be too limited, though... they all tend to work to find optimal solutions within finite domains, whereas my stuff tends 
	to be looking for one of many possible good solutions in a near-infinite domain. 
	"""
	pass

if __name__ == "__main__":
	pass