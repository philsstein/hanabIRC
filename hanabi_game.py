import logging
import random

log = logging.getLogger(__name__)

class HanabiException(Exception):
	def __init__(self, value):
		self.value = value

	def __str__(self):
		return repr(self.value)


class Card(object):

	RED = 'red'
	WHITE = 'white'
	BLUE = 'blue'
	GREEN = 'green'
	YELLOW = 'yellow'

	Colors = [RED, WHITE, BLUE, GREEN, YELLOW]


	def __init__(self, color, number):
		if not color in Card.Colors:
			raise HanabiException('bad card color: %s' % color)

		if not number in range(1,6):
			raise HanabiException('bad card number: %s' % number)

		self.color = color
		self.number = number

		# from mIRC color codes
		self._colormap = {
			Card.WHITE: 0,
			Card.BLUE: 2,
			Card.GREEN: 3,
			Card.RED: 4, 
			Card.YELLOW: 8
		}


	def __str__(self):
		return '\x03%d%2d\x03' % (self._colormap[self.color], self.number)


class Player(object):
	def __init__(self, name, hand):
		self.name = str(name)
		self.hand = hand


	def __str__(self):
		return '\x034%s\x03: %s' % (self.name, ''.join([str(c) for c in self.hand]))


class Game(object):
	def __init__(self, connection, name, channel):
		self.players = []
		self.name = name
		self.conn = connection
		self.channel = channel
		self.notes = ['w' for i in range(8)]
		self.storms = ['_' for i in range(3)]
		# The deck is Cards with color and count distributions shown, shuffled.
		self.deck = [Card(c, n) for c in Card.Colors for n in [1, 1, 1, 2, 2, 2, 3, 3, 4, 4, 5]]
		random.shuffle(self.deck)


	def show(self, nick):
		'''Show game state minus hand for nick.'''
		for p in self.players:
			#if p.name != nick:
			#	self.conn.notice(nick, '%s' % p)
			self.conn.notice(nick, '%s' % p)
			#else:
			#	self.conn.notice(nick, '%s -> ?????' % nick)

		self.conn.notice(self.channel, '%d cards remaining' % len(self.deck))
		self.conn.notice(self.channel, 'Notes: %s, Storms: %s' % (''.join(self.notes), ''.join(self.storms)))


	def add_player(self, nick):
		if len(self.players) > 5:
			self.conn.notice(nick, 'max players already in game %s. You can start another with !new [name]' % self.name)
		else:
			hand = self.deck[:5]
			self.deck = self.deck[5:]
			self.players.append(Player(nick, hand))
			self.conn.notice(nick, 'You have joined game %s' % self.name)


	def remove_player(self, nick):
		for i in self.players:
			if self.players[i].name == nick:
				self.conn.notice(nick, 'Putting %s\'s cards back in the deck.' % (self.players[i].name))
				self.deck += self.players.hand
				random.shuffle(deck)
				self.conn.notice(nick, 'Removing %s from game %s' % (self.players[i].name, self.name))
				self.players = [self.players[i] for i in self.players if self.players.name != nick]
				break


	def start_game(self):
		if len(self.players) > 0:
			self.playing = True


