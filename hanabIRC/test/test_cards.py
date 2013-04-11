#!/usr/bin/env python
'''
'''
import os
import sys
import random
import operator
sys.path.insert(0, os.path.join(sys.path[0], '..'))

from string import uppercase
from hanabi import Game, Player, Card
from text_markup import xterm_markup

# tell the cards to color for xterm
Card.markup = xterm_markup()

colors = ['red', 'white', 'blue', 'green', 'yellow'] 
card_distribution = [1, 1, 1, 2, 2, 3, 3, 4, 4, 5]
deck = [Card(c, n) for c in Game.colors for n in card_distribution]
random.shuffle(deck)

# test sort
print 'output of cards should be sorted.'
deck.sort()
for c in deck:
    print c,

print 'notes should be sorted'
notes_up, notes_down = ('w', 'b')
notes = [notes_up for i in range(8)]
storms_up, storms_down = ('X', 'O')
storms = [storms_down for i in range(3)]
