'''
Created on Jul 22, 2017

@author: Igfig
'''
import random
from dice.rollable import DiceResult 
from num2words import num2words
from dice.custom import CustomDie


class CardDeck(CustomDie):
	"""
	a 52-card deck of playing cards.
	Uses strings instead of numbers, so I don't know how well it'll work with 
	all the math.
	
	not sure exactly how to relate it to strdice yet
	"""
	def __init__(self):
		names = range(2, 10) + ['J', 'Q', 'K', 'A']
		suits = ['c', 'd', 'h', 's']
		self.cards = [str(n) + s for s in suits for n in names]
		random.shuffle(self.cards)
		self.discard = []
	
	def roll(self, num=1):
		return CardDrawResult(self.cards, num)
	
	draw = roll

class CardDrawResult(DiceResult):
	def __init__(self, deck, num):
		self.rolls = [deck.pop() for _ in range(num)]
	
	def __str__(self):
		return "\n".join(self.rolls)


class Tarokka(CardDeck):
	high_cards = ['Artifact', 'Beast', 'Broken One', 'Darklord', 'Donjon', 'Ghost', 'Executioner', 'Horseman', 'Innocent', 'Marionette', 'Mists', 'Raven', 'Tempter', 'Seer']
	common_cards = {
		'Swords' : ['Warrior', 'Avenger', 'Paladin', 'Soldier', 'Mercenary', 'Myrmidon', 'Berserker', 'Hooded One', 'Dictator', 'Torturer'],
		'Coins' : ['Rogue', 'Swashbuckler', 'Philanthropist', 'Trader', 'Merchant', 'Guilder', 'Beggar', 'Thief', 'Tax Collector', 'Miser'],
		'Stars' : ['Wizard', 'Transmuter', 'Diviner', 'Enchanter', 'Abjurer', 'Elementalist', 'Evoker', 'Illusionist', 'Necromancer', 'Conjurer'],
		'Glyphs' : ['Priest', 'Monk', 'Missionary', 'Healer', 'Shepherd', 'Druid', 'Anarchist', 'Charlatan', 'Bishop', 'Traitor']
	}
	numbers = ['Master'] + [num2words(i).capitalize() for i in range(1,11)]
	
	def __init__(self):
		self.high_deck = ["The " + card for card in self.high_cards]
		self.common_deck = [' '.join([str(index), 'of', suit, '-', 'The', name]) 
						for (suit, cards) in self.common_cards.items()
						for (index, name) in zip(self.numbers, cards)]
		self.cards = self.high_deck + self.common_deck
		random.shuffle(self.high_deck)
		random.shuffle(self.common_deck)
		random.shuffle(self.cards)
		
	def draw_high(self, num=1):
		return CardDrawResult(self.high_deck, num)
	
	def draw_common(self, num=1):
		return CardDrawResult(self.common_deck, num)
		
if __name__ == '__main__':
	t = Tarokka()
	#print(t.draw(5))
	
	common_readings, high_readings = ['Tome', 'Symbol', 'Sword'], ['Enemy', 'Battle']
	for r in common_readings:
		print(r,':', t.draw_common())
	for r in high_readings:
		print(r,':', t.draw_high())