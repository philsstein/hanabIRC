#!/usr/bin/env python

import unittest2
from string import uppercase
from hanabi import Game, Player, Card

players = ['p1', 'p2']

class test_hanabi(unittest2.TestCase):

    def setUpGame(self):
        self.game = Game()
        for p in players:
            self.game.add_player(p)

        #self.game.start_game(players[0])
        #self.game._turn_order = players
        #for c, p in zip(self.game.colors[:2], players[:2]):
        #    self.game._players[p].hand = [Card(c, i, b) for i, b in zip(xrange(1,6), ['A', 'B', 'C', 'D', 'E'])

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


if __name__ == '__main__':
    unittest2.main()

