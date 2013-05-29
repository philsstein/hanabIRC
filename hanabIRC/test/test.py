#!/usr/bin/env python
'''
    Just test for simple syntax and edge case errors 
    by running through a few scenarios.
'''
import os
import sys
sys.path.insert(0, os.path.join(sys.path[0], '..'))

from string import uppercase
from hanabi import Game, Player, Card
from text_markup import xterm_markup

# tell the cards to color for xterm
Card.markup = xterm_markup()

def display(gr):
    print '------------------'
    if not gr:
        print 'Response invalid.'
    else:
        for message in gr.public:
            print 'channel: %s' % message

        for nick, messages in gr.private.iteritems():
            for message in messages:
                print '%s: %s' % (nick, message)

def show_game(num_players, win=True):
    g = Game()
    [display(g.add_player('player_%d' % i)) for i in range(1, num_players+1)]
    p1 = g._players[g._players.keys()[0]].name
    g.start_game(p1)

    while not g._is_game_over():
        for c in ['red', 'white', 'blue', 'green', 'yellow']:
            for i in xrange(1, 6):
                # get current player
                p = g.turn_order[0]

                # card 'A' is always first. 
                g._players[p].sort_cards() 

                # the fix in in, put the in/correct card at 'A'
                if win:
                    g._players[p].hand[0] = Card(c, i, 'A')
                else:
                    g._players[p].hand[0] = Card(c, 6-i, 'A')

                print '%s playing card A' % p
                display(g.play_card(p, 'A'))
                if g._is_game_over():
                    return

# run through a bunch of games.
for w in [True, False]:
    for n in range(5, 1, -1):
        show_game(n, w)

g = Game()
display(g.add_player('Olive'))
display(g.get_hands('Olive'))
display(g.add_player('Maisie'))
display(g.add_player('Jasper'))
display(g.add_player('George'))
display(g.add_player('Frank'))
display(g.add_player('One Too Many'))
display(g.get_table())
display(g.remove_player('George'))
display(g.get_table())
display(g.start_game('Olive'))
display(g.remove_player('Maisie'))

