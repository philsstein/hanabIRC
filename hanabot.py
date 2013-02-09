'''
    hanabot.py implements an IRC bot that plays Hanabi.

    It uses the hanabi.Game module Hanabi engine to 
    get strings to display on the channel and private
    messages to the player. 

    It primarly is responsible for connecting to the 
    channel, parsing incoming commands, and writing
    reponses from the game engine.
'''    
import logging
import time
import string
import random
import sys
import os
import traceback
from hanabi import Game
from text_markup import irc_markup
from irc.bot import SingleServerIRCBot
from irc.client import VERSION as irc_client_version

log = logging.getLogger(__name__)


class Hanabot(SingleServerIRCBot):
    def __init__(self, server, channel, nick='hanabot', nick_pass=None, port=6667):
        log.debug('new bot started at %s:%d@#%s as %s', server, port,
                  channel, nick)
        SingleServerIRCBot.__init__(
            self,
            server_list=[(server, port)],
            nickname=nick,
            realname='Mumford J. Hanabot')

        self.nick_pass = nick_pass
        self.nick_name = nick  

        # force channel to start with #
        self.channel = channel if channel[0] == '#' else '#%s' % channel

        # valid bot commands
        self.commands = ['status', 'start', 'delete', 'join', 'new', 'leave',
                         'swap', 'help', 'play', 'turn', 'discard', 'hint',
                         'rules', 'game', 'st', 'sort', 'move', 'color']
        self.admin_commands = ['die', 'show']
        # these commands can execute without an active game.
        self.inactive_commands = ['new', 'help', 'rules', 'game']

        self.game = None
        self.markup = irc_markup()

    # lib IRC callbacks
    #############################################################
    def get_version(self):
        '''raises exception in lib irc, so overload in the bot.'''
        return "Python irc.bot 8.0"

    def on_nicknameinuse(self, conn, event):
        conn.nick(conn.get_nickname() + "_")

    def on_welcome(self, conn, event):
        if self.nick_pass:
            msg = 'IDENTIFY %s %s' % (self.nick_name, self.nick_pass)
            self.connection.privmsg('NickServ', msg)

        conn.join(self.channel)

    def on_kick(self, conn, event):
        time.sleep(1)
        conn.join(self.channel)
        conn.notice(self.channel, 'Why I outta....')

    def on_privmsg(self, conn, event):
        log.debug('got privmsg. %s -> %s', event.source, event.arguments)
        self.on_pubmsg(event, event)

    def on_pubmsg(self, conn, event):
        try:
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
        except Exception, e:
            log.critical('Got exception when handling message: %s' % e)

    def parse_commands(self, event, cmds):
        try:
            log.debug('got command. %s --> %s : %s',
                      event.source.nick, event.target, event.arguments)
            nick = event.source.nick
            if not cmds:
                return ([], 'Giving a command would be more useful.')

            # I don't understand when args will ever be more than just a string of
            # space separated words - need more IRC lib experience or docs.
            cmds = [str(c) for c in cmds[0].split()]

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
                                self._display(g.show_game_state(), nick)

                        return

            # valid user command check
            if not cmds[0] in self.commands or cmds[0] is not 'xyzzy':
                self._to_nick(nick, 'My dearest brother Willis, I do not '
                              'understand this "%s" of which you speak.' %
                              ' '.join(cmds))
                return

            # call the appropriate handle_* function.
            method = getattr(self, 'handle_%s' % cmds[0], None)
            if method:
                if method not in self.inactive_commands:
                    if not self.game:
                        self._to_nick(nick, 'The game is not active! Start one with !new.')
                        return
                
                # invoke it!
                method(cmds[1:], event)

        except Exception, e:
            exc_type, exc_value, exc_tb = sys.exc_info()
            filename, line_num, func_name, text = traceback.extract_tb(exc_tb)[-1]
            filename = os.path.basename(filename)
            errs = ['Exception in parse_command: %s' % e, 
                    'Error in file %s:%s in %s().' % (filename, line_num, func_name),
                    'Error text: %s' % text]
            self._to_chan('Does not compute. Unknown error happened. All bets are'
                          ' off about game(s) state. Guru contemplation haiku:')
            for err in errs:
                log.critical('%s', err)
                self._to_chan(err)

    # some sugar for sending msgs
    def _display(self, output, nick=None):
        '''Output is the list of (public, private) msgs generated
        byt the Game engine. nick is the user to priv message.
        output == (string list, string list).
        __display assumes you want to send to self.channel.'''
        for l in output[0]:
            self.connection.privmsg(self.channel, l)

        if nick:
            for l in output[1]:
                self.connection.privmsg(nick, l)

    # some sugar for sending msgs
    def _to_chan(self, msgs):
        if isinstance(msgs, list):
            self._display((msgs, []), None)
        elif isinstance(msgs, str):
            self._display(([msgs], []), None)

    # some sugar for sending strings
    def _to_nick(self, nick, msgs):
        if isinstance(msgs, list):
            self._display(([], msgs), nick)
        elif isinstance(msgs, str):
            self._display(([], [msgs]), nick)

    # Game Commands
    #############################################################
    def handle_help(self, args, event):
        log.debug('got help event. args: %s', args)
        if not args:
            usage = list()
            usage.append(
                'Below is the list of commands used during a game of Hanabi.'
                'A game is created via !new, then 2 to 5 people !join the '
                'game, and someone calls !start to start the game. Once '
                'started, the players take turns either !playing a card, '
                '!discarding a card, or giving another player a !hint. '
                'Players use !status (or !st) to view the state of the table. '
                'The game continues until the deck is empty, all the cards '
                'are correcly displayed on the table, or the three storm '
                'tokens have been flipped.')
            usage.append('Valid commands are %s' % ', '.join(self.commands))
            usage.append('Doing "!help [command]" will give details on that command.')
            self._to_nick(event.source.nick, usage)
            return

        if args[0] in Hanabot._command_usage:
            self._to_nick(event.source.nick, Hanabot._command_usage[args[0]])
        else:
            self._to_nick(event.source.nick, 'No help for topic %s' % args[0])

    def handle_hint(self, args, event):
        log.debug('got hint event. args: %s', args)
        nick = event.source.nick
        if len(args) != 2:
            self._to_nick(nick, 'bad !hint command. Must be of form !hint '
                                'nick color|number')
            return
      
        # now tell the engine about the !hint
        self._display(game.hint_player(nick, player=args[0], hint=args[1]), nick)

    def handle_rules(self, args, event):
        log.debug('got show rules event. args: %s', args)
        self._to_nick(event.source.nick, 'Go here for english rules: '
                      'http://boardgamegeek.com/filepage/59655/hanabi-'
                      'english-translation')

    def handle_game(self, args, event):    
        log.debug('got game event. args: %s', args)
        nick = event.source.nick
        state = 'being played' if self.game.has_started() else 'waiting for players'
        if not self.game.has_started():
            if len(self.game.players()):
                ps = game.players()
                s = ('Waiting for players. %d players have joined '
                     'so far, %s.' % (len(ps), ', '.join(ps)))
            else:
                s = ('Waiting for players, no players have '
                     'joined yet.')
        else:
            turn = self.game.turn(event.source.nick)[0][0]
            s = ('Game is active and being played by players %s. %s' %
                 (', '.join(self.game.players()), turn))

        self._to_chan(s)

    def _check_game_and_card(self, nick, args, cmd):
        valid_cards = ['A', 'B', 'C', 'D', 'E']
        if len(args) != 1 or len(args[0]) != 1 or not args[0] in valid_cards:
            cmd_err = ('Error in !%s command. Must be of form "!%s letter" '
                       'where the letter one of %s' % (cmd, ', '.join(valid_cards)))
            self._to_nick(nick, cmd_err)
            return False

        return True

    def handle_discard(self, args, event):
        log.debug('got discard event. args: %s', args)
        if self._check_game_and_card(event.source.nick, args, 'discard'):
            # discard the card and show the repsonse
            self._display(game.discard_card(nick, slot), nick)

            # discarding a card can trigger end game.
            if self.game.game_over()
                self.game = None 

    def handle_play(self, args, event):
        log.debug('got play event. args: %s', args)
        if self._check_game_and_card(event.source.nick, args, cmd, 'play'):
            # play the card and show the repsonse
            self._display(game.play_card(nick, slot), nick)

            # playing a card can trigger end game.
            if self.game.game_over()
                self.game = None 
    
    def handle_st(self, args, event):
        self.handle_status(args, event)

    def handle_status(self, args, event):
        ''' Show status of current game.  '''
        log.debug('got status event. args: %s', args)
        nick = event.source.nick
        self._display(self.game.get_status(nick), nick)

    def handle_xyzzy(self, args, event):
        self._to_nick(event.source.nick, 'Nothing happens.')

    def handle_new(self, args, event):
        ''' Create a new game. '''
        log.debug('got new game event')
        nick = event.source.nick
        if self.game:
            self._to_nick(nick. 'There is already an active game in the channel.')
            return 
        
        log.info('Starting new game.')
        self.game = Game(self.markup)
        pub = ['New game started by %s. Accepting joins.' % self.markup.bold(nick))]
        self._display((pub, []))

    def handle_join(self, args, event):
        '''join a game, if one is active.'''
        log.debug('got join event')
        nick = event.source.nick

        self._display(self.game.add_player(event.source.nick), nick)

    # GTL TODO: make sure this is called when the players leaves the channel
    def handle_leave(self, args, event):
        '''leave an active game.'''
        log.debug('got leave event. args: %s', args)
        nick = event.source.nick
        # remove the player and display the result
        self._display(self.game.remove_player(nick), nick)

        # removing a player can trigger end game (if there is now only one player).
        if self.game.game_over():
            self.game = None

    def handle_sort(self, args, event):
        '''arg format: []'''
        log.debug('got handle_sort event. args: %s', args)
        nick = event.source.nick
        if len(args) > 1:
            self._to_nick(nick, '(Ignoring extra arguments to !sort.)')

        self._display(game.sort_cards(nick), nick)

    def handle_move(self, args, event):
        '''arg format: from_slot to_slot'''
        log.debug('got handle_move event. args: %s', args)
        nick = event.source.nick
        if len(args) != 2:
            self._to_nick(nick, 'Error in move cmd. Should be "!move slotX '
                          'slotY" where the slots are one of A, B, C, D, E.')
            return

        self._display(game.move_card(nick, args[0], args[1]), nick)

    def handle_swap(self, args, event):
        '''arg format: from_slot to_slot [game]'''
        log.debug('got handle_swap event. args: %s', args)
        nick = event.source.nick
        if len(args) != 2:
            self._to_nick(nick, 'Error in swap cmd. Should be "!move slotX '
                          'slotY" where the slots are one of A, B, C, D, E.')
            return

        # do the swap
        self._display(game.swap_cards(nick, args[0], args[1]), nick)

    def handle_start(self, args, event):
        log.debug('got start event')
        self._display(self.game.start_game(nick), nick)

    def handle_delete(self, args, event):
        log.debug('got delete event')
        self.game = None
        self._to_chan('%s deleted game.' % (self.markup.bold(event.source.nick)))

    def handle_color(self, args, event):
        nick = event.source.nick
        pass   # GTL finish this.
                        
    ####### static class data 
    _command_usage = {
        'new': '!new - create a new game which people can join (named "game id", if given. If not given a random name will be assigned.',
        'join': '!join - join a game. If no game id, join the single game running.', 
        'start': '!start - start a game. The game must have at least two players.',
        'delete': '!delete - delete a game.', 
        'leave': '!leave - leave a game. This is bad form.', 
        'game': '!game - show the game state.', 
        'play': '!play card - play the card to the table. "card" is positional and must be one of A, B, C, D, or E.', 
        'hint': '!hint nick color|number - give a hint to a player about which color or number cards are in their hand. Valid colors: red, blue, white, green, yellow (or r, b, w, g, y) (case insensitive); valid numbers are 1, 2, 3, 4, or 5. Example "!hint frobozz blue" and "!hint plugh 4"',
        'status': '!status - show game status. (shortcut !st works as well.)',
        'st': '!status - show game status. (shortcut !st works as well.)',
        'swap': '!swap card card - swap cards in your hand. Card arguments are positional and must be one of A, B, C, D, or E.',
        'sort': '!sort - sort your cards into "correct" order, i.e. into ABCDE from "mixed" state.', 
        'move': '!move card - move a card in your hand and slide all other cards "right". "card" is positional and must be one of A, B, C, D, or E.',
        'color': '!color - toggle using color in hanabot output. Useful if you\'ve got color turned off or your client does not understand mIRC color codes.',
        'rules': '!rules - show URL for (english) Hanabi rules.', 
        'help': 'show help'
    }
