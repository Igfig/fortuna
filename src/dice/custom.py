"""
Created on May 15, 2016

@author: Igfig
"""
from dice import *; #@UnusedWildImport

class CustomDie(Die):
    """
    a die with custom sides
    """
    def __init__(self, sides):
        self.sides = sides
        self.size = len(sides)
    
    def __eq__(self, other):
        return hasattr(other, 'sides') and self.sides == other.sides 
    
    def __repr__(self):
        return "d{" + ",".join([str(s) for s in self.sides]) + "}"
    
    def roll(self, status=0):
        return DieResult(random.choice(self.sides), status)


class FateDie(Die):
    """
    a Fate die, equivalent to 1d3-2
    """
    def __init__(self):
        self.size = 1 #this may be unnecessary
    
    def __eq__(self, other):
        return isinstance(other, FateDie)
    
    def __repr__(self):
        return "dF"
    
    def roll(self, status=0):
        return DieResult(random.randint(-1, 1), status)


class DeckDraw(Die):
    """
    TODO: make this work with the existing system
    """
    
    def __init__(self, deck):
        self.deck = deck
    
    def roll(self, status=0):
        try:
            x = random.choice(self.cards) #TODO: make compatible with DieResult
            
        except ValueError:
            # no cards left in the deck
            # so shuffle the discard back into the deck
            # FIXME: this will occasionally result in drawing the same card
            # twice in one multidraw
            self.cards = self.discard
            self.discard = []
            x = random.choice(self.cards)
            
        self.cards.remove(x)
        self.discard.append(x)
        return x

if __name__ == '__main__':
    pass