"""
Created on Apr 22, 2013

Various useful collections
"""

from collections.abc import Mapping
#from nltk.chat.eliza import pairs
import random

class MultiDict(dict):
	"""a dict where you can assign multiple values to the same key
	"""
	
	def __init__(self, _dict={}):
		dict_copy = _dict.copy()
		
		for k, v in dict_copy.items():
			try:
				_ = iter(v)
			except:
				#v is not iterable, so put it in a list
				v = [v]
			finally:
				dict_copy[k] = list(v)
		
		super().__init__(dict_copy)
	
	def __setitem__(self, key, value):
		super().__setitem__(key, self.get(key, []) + [value])



class FlipDict(MultiDict):
	"""
	a MultiDict which can be flipped so that the 
	values become the keys, each mapped to a list of original keys that had that
	value in their list.
	
	TODO: make sure all values are hashable
	"""
	
	def __init__(self, _dict):
		
		super().__init__(_dict)
		self.flip = FlippedDict(self)
	
	def __setitem__(self, key, value):
		MultiDict.__setitem__(self.flip, value, key)
		return MultiDict.__setitem__(self, key, value)
	
	def __delitem__(self, key):
		for value in self[key]:
			self.flip[value].remove(key)
		return MultiDict.__delitem__(self, key)
	

class FlippedDict(FlipDict):
	def __init__(self, flipdict):
		dict.__init__(self)
		
		self.flip = flipdict
		
		for k, v in flipdict.items():
			for val in v:
				MultiDict.__setitem__(self, val, k)


"""a list with a weight for each item, for weighted random selection
TODO: needs an __add__ function"""
class WeightedList(list):
	def __init__(self, items=[], weights=[]):
		self.items = items
		self.weights = weights
		
		if len(weights) > len(items):
			del weights[len(items):]
			
		elif len(weights) < len(items):
			weights += [0] * (len(items) - len(weights))
	
	def __add__(self, other):
		pass
		#TODO: IMPLEMENT
	
	def __contains__(self, key):
		return key in self.items
	
	def __delitem__(self, key):
		del self.items[key]
		del self.weights[key]
	
	def __getitem__(self, key):
		return self.items[key]
	
	def __iter__(self): 
		for i in range(len(self.items)):
			yield (self.weights[i], self.items[i]) 
			#returns them in this order to facilitate sorting 
		
	def __len__(self):
		return len(self.items)
	
	def __repr__(self):
		out = "["
		for i in range(len(self)):
			out += str(self.items[i]) + "<" + str(self.weights[i]) + "> "
		return out.rstrip() + "]" #replacing the final space with a ]
	
	def __setitem__(self, key, item_and_weight):
		item, weight = item_and_weight
		self.items[key] = item
		self.weights[key] = weight
	
	def append(self, item, weight):
		self.items.append(item)
		self.weights.append(weight)
	
	def random_choice(self):
		upto = 0
		r = random.uniform(0, self.weight()) 
		#has to be uniform and not randint because weights might not be ints
		
		for w, i in zip(self.weights, self.items):
			if upto + w > r:
				return i
			upto += w
		assert False, "Shouldn't get here"
		
	def total_weight(self):
		return sum(self.weights)



if __name__ == "__main__":
	
	w = WeightedList(['a', 'b', 'c'], [1,2,3])
	print(w)
	
	m = MultiDict({}, WeightedList)
	m[1] = ('a', 2)
	m[1] = ('b', 1)
	print(m)
# 	f = FlipDict({
# 					'a': [1,2,3],
# 					'b': [4,2,5],
# 					'c': [3,5,3]
# 					})
# 	
# 	f['c']= 5
# 	print(f, "\n", f.flip)
	
	