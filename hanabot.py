
import logging
import time
import string
import random
from hanabi import Game
from text_markup import irc_markup
from irc.bot import SingleServerIRCBot

log = logging.getLogger(__name__)


class Hanabot(SingleServerIRCBot):
    def __init__(self, server, channel, nick='hanabot', port=6667):
        log.debug('new bot started at %s:%d@#%s as %s', server, port,
                  channel, nick)
        SingleServerIRCBot.__init__(
            self,
            server_list=[(server, port)],
            nickname=nick,
            realname='Mumford J. Hanabot')

        # force channel to start with #
        self.channel = channel if channel[0] == '#' else '#%s' % channel

        # valid bot commands
        self.commands = ['status', 'start', 'stop', 'join', 'new', 'leave',
                         'move', 'help', 'play', 'tell']
        self.admin_commands = ['die', 'show']

        # name ---> Game object dict
        self.games = {}

        self.markup = irc_markup()

        self._game_ids = self._game_name_generator()

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
        if len(a) > 1 and string.lower(a[0]) == string.lower(
                self.connection.get_nickname()):
            self.parse_commands(event, [a[1].strip()] + event.arguments[1:])

        # general channel commands
        if len(event.arguments[0]) and event.arguments[0][0] == '!':
            log.debug('got channel command: %s', event.arguments[0][1:])
            # rebuild the list w/out the ! at start of the first arg
            self.parse_commands(event,
                                [event.arguments[0][1:]] + event.arguments[1:])

    def parse_commands(self, event, cmds):
        log.debug('got command. %s --> %s : %s',
                  event.source.nick, event.target, event.arguments)
        nick = event.source.nick

        # I don't understand when args will ever be more than just a string of
        # space separated words
        cmds = cmds[0].split()

        # op only commands - return after executing.
        if cmds[0] in self.admin_commands:
            log.debug('running admin cmd %s', cmds[0])
            for chname, chobj in self.channels.items():
                if nick in chobj.opers():
                    if cmds[0] == 'die':
                        self.die('Seppuku Successful')
                    elif cmds[0] == 'show':
                        for name, g in self.games.iteritems():
                            log.debug('Showing state for game %s', name)
                            for l in g.show_game_state():
                                self.connection.notice(nick, l)
                    return

        # user commands
        if not cmds[0] in self.commands:
            self.connection.notice(nick, 'My dearest brother Willis, I do not'
                                   ' understand this "%s" of which you speak.'
                                   % ' '.join(cmds))
            return

        # call the appropriate handle_* function.
        method = getattr(self, 'handle_%s' % cmds[0], None)
        if method:
            method(cmds[1:], event)

    # Game Commands
    #############################################################

    def handle_help(self, args, event):
        log.debug('got help event. args: %s', args)
        nick = event.source.nick
        usage = ['All commands end optionally with a gameid.',
                 'Your IRC client must display mIRC colors to play.',
                 '------------',
                 '!new [gameid] - start a new game (named gameid, if given).',
                 '!join [gameid] - join a game. If no gameid, join the single'
                 ' game running.',
                 '!leave [gameid] - leave a game.',
                 '!move slotA slotB [gameid] - within your hand move cards,',
                 '!tell nick color|numner slotA slotB ... slotN [gameid]',
                 '!play slotN [gameid] - play a card to the table.',
                 '!status [gameid] - show game status.',
                 '!show [gameid] - show all game status, including hands'
                 'and deck.']

        for l in usage:
            self.connection.notice(nick, l)

    def handle_play(self, args, event):
        log.debug('got play event. args: %s', args)
        if 0 == len(args) or len(args) > 2:
            return ['You must specify only a slot number (and optionally '
                    'a game id).']

        game_name = args[1] if len(args) == 2 else None
        nick = event.source.nick
        game = self._get_game(game_name, nick)
        if not game:
            return ['Unable to find game.']     # GTL fix

        try:
            slot = int(args[0])
        except ValueError:
            self.connection.notice(nick, '!play slot must be an integer.')
            return

        if slot <= 0 or slot >= 6:
            self.connection.notice(nick, '!play slot must be between 1 and 5.')
            return

        # play the card and show the repsonse
        for l in game.play_card(nick, slot):
            self.connection.notice(self.channel, l)

    def handle_tell(self, args, event):
        pass

    def handle_status(self, args, event):
        '''
        Show status of all/one of games user is playing in.
            args: [name]
        If game name is given, show just that game status.
        '''
        log.debug('got status event. args: %s', args)
        nick = event.source.nick
        if not len(self.games):
            self.connection.notice(nick, 'There are no active games! '
                                   'You can start one with !new [game]')
            return

        game_name = None if len(args) == 0 else args[0]
        for name, g in self.games.iteritems():
            if g.in_game(nick):
                if (game_name and game_name == name) or not game_name:
                    for l in g.get_status(nick):
                        self.connection.notice(nick, l)

    def handle_new(self, args, event):
        '''
        Create a new game.
            args: [game name]
        If given, use the name as to id the game instance.
        '''
        log.debug('got new game event')
        game_name = None if len(args) == 0 else args[0]
        nick = event.source.nick
        if not game_name:
            game_name = self._game_ids.next()

        if game_name in self.games.keys():
            self.connection.notice(nick, 'The game %s already exists.' %
                                   self.markup.bold(game_name))
        else:
            log.info('Starting new game %s' % self.markup.bold(game_name))
            self.games[game_name] = Game(game_name, self.markup)
            self.connection.notice(self.channel, 'New game "%s" started by %s.'
                                   'Accepting joins now.' %
                                   (self.markup.bold(game_name), nick))

    def handle_join(self, args, event):
        '''args: [game]'''
        log.debug('got join event')

        if not len(self.games):
            self.connection.notice(event.source.nick, 'There are no games'
                                   ' going on! Start one with !new [name]')
            return

        nick = event.source.nick
        if len(args) == 0 and len(self.games) > 1:
            self.connection.notice(nick, 'You must specify a game via "!join '
                                   'game" as there is more than one game going'
                                   ' on.')
            return

        game_name = None if len(args) == 0 else args[0]
        game = self._get_game(game_name, nick)
        if not game:
            return

        for l in game.add_player(event.source.nick):
            self.connection.notice(self.channel, l)

    def handle_leave(self, args, event):
        '''args: game to leave. If not given leave all games.'''
        log.debug('got leave event. args: %s', args)
        nick = event.source.nick
        game_name = None if len(args) == 0 else args[0]
        if not game_name:
            # remove player from all games.
            for game in self.games.values():
                if game.in_game(nick):
                    for l in game.remove_player(nick):
                        self.connection.notice(self.channel, l)

                    self.connection.notice(nick, 'You have been removed from '
                                           'game %s.' %
                                           self.markup.bold(game_name))
            return

        game = self._get_game(game_name, nick)
        if not game:
            return

        for l in game.remove_player(nick):
            self.connection.notice(self.channel, l)

        self.connection.notice(nick, 'You have been removed from game %s.' %
                               self.markup.bold(game_name))

    def handle_move(self, args, event):
        '''arg format: from_slot to_slot [game]'''
        log.debug('got handle_move event. args: %s', args)
        nick = event.source.nick
        err_mess = 'Error in move cmd. Should be !move from to [game]'
        if len(args) != 2 and len(args) != 3:
            self.connection.notice(nick, err_mess)
            return

        try:
            from_slot = int(args[0])
            to_slot = int(args[1])
        except ValueError:
            self.connection.notice(nick, '!move args must be integers between '
                                   '1 and 5.')
            return

        if from_slot < 0 or from_slot > 5 or to_slot < 0 or to_slot > 5:
            self.connection.notice(nick, '!move args must be between 1 and 5.')
            return

        game_name = args[2] if len(args) == 3 else None
        game = self._get_game(game_name, nick)
        if not game:
            return

        # and finally do the move.
        for l in game.move_card(nick, from_slot, to_slot):
            self.connection.notice(self.channel, l)

    def handle_start(self, args, event):
        log.debug('got start event')
        nick = event.source.nick
        game_name = None if len(args) == 0 else args[0]
        game = self._get_game(game_name, nick)
        if not game:
            return

        for l in game.start_game():
            self.connection.notice(self.channel, 'Game %s started!' %
                                   (self.markup.bold(game.name)))

    def handle_stop(self, args, event):
        log.debug('got stop event')
        nick = event.source.nick
        game_name = None if len(args) == 0 else args[0]
        game = self._get_game(game_name, nick)
        if not game:
            return

        for l in game.stop_game():
            self.connection.notice(self.channel, l)

    def _get_game(self, name, nick):
        '''Given the name, find the referenced game. The name can be None
        in which case the first game is returned. If there are no games,
        None is returned. On error, a notice is sent to nick.'''

        # the cases:
        #   no games: fail no games running.
        #   no name given and only one game, return game else fail 'more
        #       than one game'
        #   name given: if found return game, else fail 'that game not found'
        if len(self.games) == 0:
            self.connection.notice(nick, 'No games available. Start a one with'
                                   ' !new [gameID]')
            return None

        if not name:
            if len(self.games) == 1:
                return self.games[self.games.keys()[0]]
            else:
                self.connection.notice(nick, 'More than one active game, '
                                       'specify which with the gameID')
                return None

        # at this point we know name is not None
        if name in self.games:
            log.debug('Found game %s for nick %s', name, nick)
            return self.games[name]
        else:
            self.connection.notice(nick, 'GameID %s not found.' %
                                   (self.markup.bold(name)))
            return None

    def _game_name_generator(self):
        # GTL TODO: make this into a pool instead of just a generator
        names = ['buffy', 'xander', 'willow', 'tara', 'anyanka', 'spike',
                 'giles', 'angel', 'mal', 'wash', 'simon', 'kaylee', 'zoe',
                 'river', 'book', 'inara', 'jayne', 'cordelia', 'oz', 'anya',
                 'dawn', 'the_master', 'drusilla', 'darla', 'the_mayor',
                 'adam', 'glory', 'joyce', 'jenny', 'wesley', 'harmony',
                 'kendra', 'olive', 'maisie']

        i = 0
        while True:
            random.shuffle(names)
            for n in names:
                if i == 0:
                    yield n
                else:
                    yield '%s_%d' % (n, i)
            else:
                i += 1
