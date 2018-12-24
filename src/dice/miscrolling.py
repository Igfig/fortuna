import random
from dice.rollable import *
from dice.strings import *

for i in range(500): 
	print(random.randint(1, 20))
 	#print(Die(12).roll() + Die(8).roll())