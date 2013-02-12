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
from collections import defaultdict

from hanabi import Game
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
        self.command_dict = {
            'Game Management': ['new', 'delete', 'join', 'start', 'leave'],
            'Hand Management': ['move', 'swap', 'sort'],
            'Game Action': ['play', 'hint', 'discard'],
            'Information': ['help', 'rules', 'turn', 'game', 'hands',
                            'table', 'discardpile']
        }
        
        self.commands = list()
        for cmds in self.command_dict.values():
            self.commands += cmds

        self.commands_admin = ['die']

        # these commands can execute without an active game.
        self.no_game_commands = ['new', 'help', 'rules', 'game']

        self.game = None

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
            if cmds[0] in self.commands_admin:
                log.debug('running admin cmd %s', cmds[0])
                for chname, chobj in self.channels.items():
                    if nick in chobj.opers():
                        if cmds[0] == 'die':
                            self.die('Seppuku Successful')

                        return

            # valid user command check
            if not cmds[0] in self.commands:
                self._to_nick(nick, 'My dearest brother Willis, I do not '
                              'understand this "%s" of which you speak.' %
                              ' '.join(cmds))
                return

            # call the appropriate handle_* function.
            method = getattr(self, 'handle_%s' % cmds[0], None)
            if method:
                if not cmds[0] in self.no_game_commands and not self.game:
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
                'A game is created via !new, then 2 to 5 people !join the '
                'game, and someone calls !start to start the game. Once '
                'started, players take turns either !playing a card, '
                '!discarding a card, or giving another player a !hint. '
                'After a valid !play or !discard the state of the '
                'table is shown along with next turn ordering. (The table '
                'state can also be seen with the !table command.')
            usage.append(
                'Players can use !hands to view all hands at the table, '
                'including their own. Your own hand is shown with the "backs" '
                'facing you. Each card is assigned a letter A-E and "tracks" as '
                'the cards in your hand move around. You reference your own '
                'hands via these letters, e.g. "!play C" or "!discard A"')
            usage.append(
                'Hints are given by the !hint command. The hint format '
                'is "!hint nick color|number". Valid numbers are 1-5; '
                'valid colors are white, yellow, red, blue, or green.'
                ' Example: "!hint xyzzy blue" or "!hint fred 3"')
            usage.append(
                'The game continues until the deck is empty, all the cards '
                'are correcly displayed on the table, or the three storm '
                'tokens have been flipped.')
            for text, cmds in self.command_dict.iteritems():
                usage.append('%s commands: %s' % (text, ', '.join(cmds)))

            usage.append('Doing "!help [command]" will give details on that command.')
            self._to_nick(event.source.nick, usage)
            return

        if args[0] in Hanabot._command_usage:
            self._to_nick(event.source.nick, Hanabot._command_usage[args[0]])
        else:
            self._to_nick(event.source.nick, 'No help for topic %s' % args[0])

    def handle_hint(self, args, event):
        log.debug('got hint event. args: %s', args)
        if not self._check_args(args, 2, [str, str], event, 'hint'):
            return 

        # now tell the engine about the !hint
        nick = event.source.nick
        self._display(self.game.hint_player(nick, player=args[0], hint=args[1]), nick)

    def handle_rules(self, args, event):
        log.debug('got rules event. args: %s', args)
        if not self._check_args(args, 0, [], event, 'rules'):
            return 

        self._to_nick(event.source.nick, 'Go here for english rules: '
                      'http://boardgamegeek.com/filepage/59655/hanabi-'
                      'english-translation')

    def handle_game(self, args, event):    
        log.debug('got game event. args: %s', args)
        if not self._check_args(args, 0, [], event, 'game'):
            return 

        if not self.game:
            self._to_chan('There is no game being played. Use !new to start one.')
            return 

        state = 'being played' if self.game.has_started() else 'waiting for players'
        if not self.game.has_started():
            if len(self.game.players()):
                ps = self.game.players()
                s = ('Waiting for players. %d players have joined '
                     'so far: %s.' % (len(ps), ', '.join(ps)))
            else:
                s = ('Waiting for players, no players have '
                     'joined yet.')
        else:
            turn = self.game.turn(event.source.nick)[0][0]
            s = ('Game is active and being played by players %s. %s' %
                 (', '.join(self.game.players()), turn))

        self._to_chan(s)

    def handle_turn(self, args, event):
        if not self._check_args(args, 0, [], event, 'turn'):
            return 

        self._display(self.game.turn(event.source.nick), event.source.nick)

    def handle_table(self, args, event):
        log.debug('got table command.')
        if not self._check_args(args, 0, [], event, 'table'):
            return 

        self._display(self.game.get_table(), event.source.nick)

    def handle_discard(self, args, event):
        log.debug('got discard event. args: %s', args)
        if not self._check_args(args, 1, [str], event, 'discard'):
            return 

        # discard the card and show the repsonse
        nick = event.source.nick
        self._display(self.game.discard_card(nick, args[0]), nick)

        # discarding a card can trigger end game.
        if self.game.game_over():
            self.game = None 

    def handle_play(self, args, event):
        log.debug('got play event. args: %s', args)
        # play the card and show the repsonse
        if not self._check_args(args, 1, [str], event, 'play'):
            return 

        nick = event.source.nick
        self._display(self.game.play_card(nick, args[0]), nick)

        # playing a card can trigger end game.
        if self.game.game_over():
            self.game = None 
    
    def handle_hands(self, args, event):
        ''' Show hands of current game.  '''
        log.debug('got hands event. args: %s', args)
        if not self._check_args(args, 0, [], event, 'hands'):
            return 

        nick = event.source.nick
        self._display(self.game.get_hands(nick), nick)

    def handle_xyzzy(self, args, event):
        self._to_nick(event.source.nick, 'Nothing happens.')

    def handle_new(self, args, event):
        ''' Create a new game. '''
        log.debug('got new game event')
        if not self._check_args(args, 0, [], event, 'new'):
            return 

        nick = event.source.nick
        if self.game:
            self._to_nick(nick, 'There is already an active game in the channel.')
            return 
        
        log.info('Starting new game.')
        self.game = Game()
        pub = ['New game started by %s. Accepting joins.' % nick]
        self._display((pub, []))

    def handle_join(self, args, event):
        '''join a game, if one is active.'''
        log.debug('got join event')
        if not self._check_args(args, 0, [], event, 'join'):
            return 

        nick = event.source.nick
        self._display(self.game.add_player(nick), nick)

    # GTL TODO: make sure this is called when the players leaves the channel?
    def handle_leave(self, args, event):
        '''leave an active game.'''
        log.debug('got leave event. args: %s', args)
        if not self._check_args(args, 0, [], event, 'leave'):
            return 

        nick = event.source.nick
        # remove the player and display the result
        self._display(self.game.remove_player(nick), nick)

        # removing a player can trigger end game (if there is now only one player).
        if self.game.game_over():
            self.game = None

    def handle_sort(self, args, event):
        '''arg format: []'''
        log.debug('got handle_sort event. args: %s', args)
        if not self._check_args(args, 0, [], event, 'sort'):
            return 

        nick = event.source.nick
        self._display(self.game.sort_cards(nick), nick)

    def handle_move(self, args, event):
        '''arg format: cardX slotN.'''
        log.debug('got handle_move event. args: %s', args)
        if not self._check_args(args, 2, [str, int], event, 'move'):
            return 

        nick = event.source.nick
        self._display(self.game.move_card(nick, args[0], args[1]), nick)

    def handle_swap(self, args, event):
        '''arg format: cardA cardB.'''
        log.debug('got handle_swap event. args: %s', args)
        if not self._check_args(args, 2, [str, str], event, 'swap'):
            return 

        # do the swap
        nick = event.source.nick
        self._display(self.game.swap_cards(nick, args[0], args[1]), nick)

    def handle_start(self, args, event):
        log.debug('got start event')
        if not self._check_args(args, 0, [], event, 'start'):
            return 

        nick = event.source.nick
        self._display(self.game.start_game(nick), nick)

    def handle_delete(self, args, event):
        log.debug('got delete event')
        if not self._check_args(args, 0, [], event, 'delete'):
            return 

        self.game = None
        self._to_chan('%s deleted game.' % event.source.nick)

    def handle_discardpile(self, args, event):
        log.debug('got discardpile event')
        if not self._check_args(args, 0, [], event, 'discardpile'):
            return 

        nick = event.source.nick
        self._display(self.game.get_discard_pile(), nick)

    def _check_args(self, args, num, types, event, cmd):
        '''Check the given arguments for correct types and number. Show error
        message and help to nick on error and return False. Else return True. 
        As a side effect, set the types correctly. e.g. "1.2" is set to 1.2.'''
        if len(args) != num:
            self._to_nick(event.source.nick, 'Wrong number of arguments to %s' % cmd)
            self.handle_help([cmd], event)
            return False
        elif len(types) != num:
            # This is an internal callee error, so no message. 
            log.info('internal error in _check_args: wrong number of types passed in.')
            return False

        for i in xrange(len(args)):
            try:
                args[i] = types[i](args[i])
            except ValueError:
                self._to_nick(event.source.nick, 'Wrong type for argument %s in command %s.' % (args[i], cmd))
                self.handle_help([cmd], event)
                return False

        return True

    ####### static class data 
    _command_usage = {
        'new': '!new - create a new game which people can join. One game per channel.',
        'delete': '!delete - delete a game.', 
        'join': '!join - join a game. If not game in channel, use !new to create one.', 
        'start': '!start - start a game. The game must have at least two players.',
        'leave': '!leave - leave a game. This is bad form.', 
        'move': '!move card - move a card in your hand and slide all other cards "right". "card" must be one of A, B, C, D, or E. "index" is where to put the card, counting from the left and must be an integer between 1 and max hand size.',
        'swap': '!swap card card - swap cards in your hand. Card arguments must be one of A, B, C, D, or E.',
        'sort': '!sort - sort your cards into "correct" order, i.e. into ABCDE order from "mixed" state.', 
        'play': '!play card - play the card to the table. "card" must be one of A, B, C, D, or E.', 
        'hint': '!hint nick color|number - give a hint to a player about which color or number cards are in their hand. Valid colors: red, blue, white, green, yellow (or r, b, w, g, y) (case insensitive); valid numbers are 1, 2, 3, 4, or 5. Example "!hint frobozz blue" and "!hint plugh 4"',
        'discard': '!discard card - place a card in the discard pile. "card" must be one of A, B, C, D, or E.', 
        'help': 'Infinite recursion detected. Universe is rebooting...',
        'rules': '!rules - show URL for (english) Hanabi rules.', 
        'turn': '!turn - show which players turn it is.', 
        'game': '!game - show the game state.', 
        'hands': '!hands - show hands of players. Your own hand will be shown with the "backs" facing you, identified individually by a letter. When a card is removed the letter is reused for the new card.',
        'table': '!game - show the state of the table', 
        'discardpile': '!discardpile - show the current discard pile.',
        'grue': 'You are likely to be eaten.',
    }
