#!/usr/bin/env python

import os
import sys
sys.path.insert(0, os.path.join(sys.path[0], '..'))

import unittest2
from string import uppercase
from hanabi import Game, Player, Card
from text_markup import xterm_markup, text_markup_base

players = ['p1', 'p2']

class test_hanabi(unittest2.TestCase):

    def setUpGame(self):
        self.game = Game()
        for p in players:
            self.game.add_player(p)

        self.game.start_game(players[0])
        self.game.turn_order = list(players)

    def getHand(self, h):
        return ' '.join([str(c) for c in h])

    def getBacks(self, h):
        return ''.join([c.back() for c in h])
    
    def getFronts(self, h):
        return ''.join([c.front() for c in h])

    def test_handmgt(self):
        p = Player(players[0])
        p.hand = [Card('red', i, b) for i, b in zip(xrange(1,6), uppercase[:5])]
        self.assertEqual('ABCDE', self.getBacks(p.hand))

        print p.swap_cards('A', 'E')
        self.assertEqual('EBCDA', self.getBacks(p.hand))

    def test_play(self):
        self.setUpGame()
        print self.game.turn()
        print self.game.play_card(players[0], 'A')
        print self.game.turn()
        print self.game.hint_player(players[1], players[0], 'blue')

    def test_lastround(self):
        # Make the deck have one card, let a player discard.
        # Then make sure each player (inc. initial one) gets one
        # more turn.
        self.setUpGame()
        self.game.deck = [Card('red', 1, 'A')]
        self.game.discard_card(self.game.player_turn(), 'A')
        for i in xrange(len(players)):
            self.assertFalse(self.game.game_over())
            self.game.discard_card(self.game.player_turn(), 'A')

        self.assertTrue(self.game.game_over())

    def test_rainbow_display(self):
        p = Player(players[0])
        p.hand = [Card('rainbow', i, b) for i, b in zip(xrange(1,6), uppercase[:5])]
        m = xterm_markup()
        print m.color('hello world', xterm_markup.RAINBOW)

        self.game = Game()
        self.game.markup = m
        for p in players:
            self.game.add_player(p)

        for c in self.game.deck:
            c.markup = self.game.markup

        self.game.start_game(players[0], opts={'rainbow_10': True})
        self.game.turn_order = list(players)
        for n, l in [(1, 'A'), (2, 'B'), (3, 'C')]:
            c = Card(text_markup_base.RAINBOW, n, l)
            c.markup = self.game.markup
            self.game._players[self.game.player_turn()].hand[n-1] = c
        self.game.play_card(self.game.player_turn(), 'A')
        self.game.play_card(self.game.player_turn(), 'A')
        print self.game.play_card(self.game.player_turn(), 'B')

if __name__ == '__main__':
    unittest2.main()

