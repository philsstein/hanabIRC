
import logging
import irc
import time
import string
import random
from hanabi_game import Game
from text_markup import irc_markup
from irc.bot import SingleServerIRCBot

log = logging.getLogger(__name__)

class Hanabot(SingleServerIRCBot):
	def __init__(self, server, channel, nick='hanabot', port=6667):
		log.debug('new bot started at %s:%d@#%s as %s', server, port, channel, nick)
		SingleServerIRCBot.__init__(self,
			server_list = [(server, port)], 
			nickname = nick,
			realname = 'Mumford J. Hanabot')

		# force channel to start with #
		self.channel = channel if channel[0] == '#' else '#%s' % channel

		# valid bot commands
		self.commands = ['status', 'start', 'stop', 'join', 'new', 'leave']
		self.admin_commands = ['die', 'show']

		# name ---> Game object dict
		self.games = {}
	
	# lib IRC callbacks
	#############################################################

	def on_nicknameinuse(self, conn, event):
		conn.nick(conn.get_nickname() + "_")


	def on_welcome(self, conn, event):
		conn.join(self.channel)		


	def on_kick(self, conn, event):
		time.sleep(1)
		conn.join(self.channel)
		conn.notice(self.channel, 'Why I outta....')


	def on_privmsg(self, conn, event):
		log.debug('got privmsg. %s -> %s', event.source, event.arguments)
		self.parse_commands(event, event.arguments)


	def on_pubmsg(self, conn, event):
		log.debug('got pubmsg. %s -> %s', event.source, event.arguments)
		# messaged commands
		a = event.arguments[0].split(':', 1)
		if len(a) > 1 and irc.strings.lower(a[0]) == irc.strings.lower(self.connection.get_nickname()):
			self.parse_commands(event, [a[1].strip()] + event.arguments[1:])

		# general channel commands
		if len(event.arguments[0]) and event.arguments[0][0] == '!':
			log.debug('got channel command: %s', event.arguments[0][1:])
			# rebuild the list w/out the ! at start of the first arg
			self.parse_commands(event, [event.arguments[0][1:]] + event.arguments[1:])


	def parse_commands(self, event, cmds):
		log.debug('got command. %s --> %s : %s', event.source.nick, event.target, event.arguments)
		nick = event.source.nick

		# I don't understand when args will ever be more than just a string of space separated words
		cmds = cmds[0].split()

		# op only commands - return after executing.
		if cmds[0] in self.admin_commands:
			for chname, chobj in self.channels.items():
				if nick in chobj.opers():
					if cmds[0] == 'die':
						self.die('Seppuku Complete')
					elif cmds[0] == 'show': 
						for g in self.games.values():
							g.show_game_state()

					return	
	
		# user commands
		if not cmds[0] in self.commands:
			self.connection.notice(nick, 'My dearest brother Willis, I do not understand this "%s" of which you speak.' % ' '.join(cmds))
			return

		# call the appropriate handle_* function. 
		method = getattr(self, 'handle_%s' % cmds[0], None)
		if method:
			method(cmds[1:], event)

	# Game Commands
	#############################################################

	def handle_status(self, args, event):
		'''
		Show status of all/one of games user is playing in.
			args: [name (optional)]
		If game name is given, show just that game status. 		
		'''	
		log.debug('got status event')
		game_name = None if len(args) == 0 else args[0]
		nick = event.source.nick
		for g in self.games:
			if nick in g.players:
				if (game_name and game_name == g.name) or not game_name:
					for l in g.get_status(nick):
						self.connection.notice(nick, l)

	def handle_new(self, args, event):
		''' 
		Create a new game. 
			args: [game name]
		If given, use the name as to id the game instance. 
		'''
		log.debug('got new game event')
		game = None if len(args) == 0 else args[0]
		nick = event.source.nick
		if not game: 
			game = ''.join(random.choice(string.lowercase) for i in range(8))

		if game in self.games.keys():
			self.connection.notice(nick, 'The game %s already exists.' % game)
		else:
			log.info('Starting new game %s' % game)
			self.games[game] = Game(game, irc_markup())
			self.connection.notice(self.channel, 'New game "%s" started by %s. Accepting joins now.' % (nick, game))


	def handle_join(self, args, event):
		'''args: [game]'''
		log.debug('got join event')

		if not len(self.games):
			self.connection.notice(event.source.nick, 'There are no games going on! Start one with !new [name]')
			return


		if len(args) == 0 and len(self.games) > 1: 
			self.connection.notice(event.source.nick, 'You must specify a game "!join game" as there is more than one game going on.')
			return
		
		game = self.games.keys()[0] if len(args) == 0 else args[0]

		if not game in self.games.keys():
			self.connection.notice(event.source.nick, 'No such game: %s' % game)
		else:
			self.games[game].add_player(event.source.nick)


	def handle_leave(self, args, event):
		'''args: game to leave. If not given leave all games.'''
		log.debug('got leave event')
		game = args[0]
		if not game:
			for game in self.games.values():
				game.remove_player(event.source.nick)
		else:
			if not game in self.games.keys():
				self.connection.notice('Game %s does not exist.' % game)
			else:
				self.games[game].remove_player(event.source.nick)


	def handle_start(self, args, event):
		log.debug('got start event')


	def handle_stop(self, args, event):
		log.debug('got stop event')



