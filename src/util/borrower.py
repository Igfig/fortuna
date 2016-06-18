"""
Created on Mar 21, 2015

@author: Ira
"""

import inspect

class Borrower:
	def __init__(self, harvestee, checkparents=True):
		self.harvestee = harvestee
		self.checkparents = checkparents
		self.queue = []
	
	def __getattr__(self, name):
		for member in inspect.getmembers(self.harvestee):
			if member[0] == name:
				realattr = member[1]
				
				if callable(realattr):
					return self.harvest_args_from(name)
				else:
					return realattr
		
		raise AttributeError
		
		"""
		realattr = self.harvestee.__dict__[name]
		
		if callable(realattr):
			return self.harvest_args_from(name)
		else:
			return realattr
		"""
	
	def harvest_args_from(self, fname):
		def harvest_args(*args, **kwargs):
			self.queue.append(StoringMethodCaller(fname, *args, **kwargs))
			return self
		return harvest_args

class StoringMethodCaller:
	"""
	Return a callable object that calls the given method on its operand.
	After f = methodcaller('name'), the call f(r) returns r.name().
	After g = methodcaller('name', 'date', foo=1), the call g(r) returns
	r.name('date', foo=1).
	"""

	def __init__(*args, **kwargs): # @NoSelf
		if len(args) < 2:
			msg = "methodcaller needs at least one argument, the method name"
			raise TypeError(msg)
		self = args[0]
		self.name = args[1]
		self.args = args[2:]
		self.kwargs = kwargs

	def __call__(self, obj):
		return getattr(obj, self.name)(*self.args, **self.kwargs)
