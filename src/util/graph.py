"""
Created on Mar 27, 2013

@author: Ira Fich
"""

class BipartiteGraph(object):
	"""
	Base class for bipartite graphs
	"""


	def __init__(self, left, right):
		"""
		@param left:  dict of left-side node names and the names of the right-side nodes they touch
		@param right: the converse
		"""
		
		self.left  = {name:BGNode(name, neighbours) for name, neighbours in left.items()}
		self.right = {name:BGNode(name, neighbours) for name, neighbours in right.items()}



class BGNode(object):
	
	def __init__(self, name, neighbours=[], standsfor=[]):
		self.identity = name
		self.neighbours = neighbours
		self.standsfor = standsfor
	
	def __repr__(self):
		return `self.neighbours` + "/" + `self.standsfor`