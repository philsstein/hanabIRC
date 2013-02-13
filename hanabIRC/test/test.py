#!/usr/bin/env python
'''
    Just test for simple syntax and edge case errors 
    by running through a few scenarios.
'''
from string import uppercase
from hanabi import Game, Player, Card

def display(lists):
    for lines in [('Public:', lists[0]), ('Private:', lists[1])]:
        print lines[0]
        if not len(lines[1]):
            print '\t ---'
        else:
            for l in lines[1]:
                print '\t', l

def show_hands(g):
    hands = [p.get_hand() for p in g._players.values()]
    hidden = [p.get_hand(hidden=True) for p in g._players.values()]
    print ' --- '
    print ' Hands: %s' % ', '.join(hands)
    print 'Hidden: %s' % ', '.join(hidden)
    print ' --- '

def show_game(num_players, win=True):
    g = Game()
    [display(g.add_player('player_%d' % i)) for i in range(1, num_players+1)]
    p1 = g._players[g._players.keys()[0]].name
    g.start_game(p1)

    while not g._is_game_over():
        for c in Game.colors:
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

                show_hands(g)
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

