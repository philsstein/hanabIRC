'''
    hanabi.py implements the logic of the game Hanabi.

    It exports an API for player and card management. The API
    generally returns arrays of strings suitable for display to 
    game players. These strings can be dumped to an IRC channel,
    or directly to a socket, stdout, etc. 

    The general play sequence is: 
        add players
        start game
        in turn order a player:
            plays a card to the table or
            hints a another player about their hand (this is 
                not handled by the Game engine) or
            discards a card

        The game ends when a player plays a card incorrectly
        to the table three times, as shown by the Storm tokens or
        the draw deck is empty.

        There is group scoring and the score is based on the 
        number of legally played cards on the table at the end 
        of the game.

'''
import logging
import random
import string
from GameResponse import GameResponse as gr
from text_markup import irc_markup
from collections import defaultdict

log = logging.getLogger(__name__)

class Card(object):
    '''
    Card has a color, a number, and a "mark". The mark is a char that 
    represents the card, think the image of the char on the back of the card.
    '''
    markup = irc_markup()

    def __init__(self, color, number, mark=None):
        self.color = color
        self.number = number
        self.mark = mark
        self.markup = Card.markup

    def front(self):
        # special case rainbow.
        if self.color == 'rainbow':
            return '%s%d' % ('RNBW', self.number)
        else:
            return self.markup.color('%s%d' % (self.color[0].upper(), self.number), self.color)

    def back(self):
        return '%s' % self.mark

    def __str__(self):
        return '%s/%s' % (self.front(), self.back())

class Player(object):
    '''
        If the player themselves is requesting to see the hand, they get
        an opaque hand. If anyone else wants to see it, they see it all.

        Players can modify the order of cards in their own hands as well.
    '''
    def __init__(self, name):
        self.name = str(name)
        # The player's hand, a list of Cards
        self.hand = list()

    def sort_cards(self):
        '''
        re-sort the card into "orginal" positions.
        '''
        self.hand = sorted(self.hand, key=lambda x: x.mark)
        return gr(private={self.name: 'Your cards have been sorted.'})

    def card_index(self, X):
        # ugly, sorry. Works well though.
        return next((i for i, c in enumerate(self.hand) if c.mark == X.upper()), None)

    def swap_cards(self, A, B):
        '''swap a card within a hand. output is for the group. A and B
        are the position-based index of the cards.'''
        i = self.card_index(A.upper())
        j = self.card_index(B.upper())
        if i is None or j is None:
            message = '!swap card argument must be one of %s' % ', '.join(sorted([c.mark for c in self.hand]))
            return gr(private={self.name: message})

        self.hand[i], self.hand[j] = self.hand[j], self.hand[i]
        return gr(private={self.name:'Swapped cards %s and %s' % (A, B)})

    def move_card(self, A, i):
        '''swap a card within a hand. A is the card, i is the 1-based index or where
        to put it within the hand.'''
        try:
            i = int(i)
        except ValueError:
            return gr(private={self.name:'move index arugment must be an integer.'})

        if not (1 <= i <= len(self.hand)):
            message = 'move index argument must between 1 and %d' % len(self.hand)
            return gr(private={self.name: message})

        j = self.card_index(A.upper())
        if j is None:
            message = 'move card argument must be one of %s' % ', '.join(sorted([c.mark for c in self.hand]))
            return gr(private={self.name: message})

        self.hand.insert(i-1, self.hand.pop(j))
        return gr(private={self.name: 'Moved card %s to position %d.' % (A, i)})

    def get_hand(self, hidden=False):
        '''return the hand as a string.'''
        if not self.hand:
            return 'No hand dealt yet.'

        if not hidden:
            return '%s: %s' % (self.name, ' '.join([str(c) for c in self.hand]))
        else:
            return '%s: %s' % (self.name, ''.join([c.back() for c in self.hand]))

    def add_card(self, card):
        '''Add a card to a player's hand. This method marks the back of the card
        appropriately and is the only way you should add cards to a player's hand.'''
        # use sets to find the missing mark
        missing = set(string.uppercase[:len(self.hand)+1]) - set([c.mark for c in self.hand])

        if len(missing) != 1:
            log.info('Error: adding card to player\'s hand')
            return

        # simply append the card after marking it.
        card.mark = list(missing)[0]
        self.hand.append(card)


class Game(object):
    '''
        The Game itself. Keeps track of players, turns, and cards.
        Returns lists of strings that describe current game state.

        Most functions return a pair of list of strings. The first
        is for public display, the second for display to the player.

        Example:
        (pub, priv) = game.function(...)
        show_user(priv)
        show_all(pub)

        See below for extended usage sample. In this example the "..."
        is filled with a card or list of cards. (doctest needs the ...
        evaluate the statements correctly as the cards change everytime.

        Example:
        TODO: doctest sample here.
    '''
    # "static" class variables.
    colors = ['red', 'white', 'blue', 'green', 'yellow'] 
    card_distribution = [1, 1, 1, 2, 2, 3, 3, 4, 4, 5]

    def __init__(self):
        '''
            Later may take variants as args so something.
        '''
        self._players = defaultdict(str)
        # turn_order[0] is always current player's name
        self.turn_order = []
        self.max_players = 5

        self.notes_up, self.notes_down = ('w', 'b')
        self.notes = [self.notes_up for i in range(8)]
        self.storms_up, self.storms_down = ('X', 'O')
        self.storms = [self.storms_down for i in range(3)]
        
        # The deck is Cards with color and count distributions shown, shuffled.
        self.deck = [Card(c, n) for c in Game.colors
                     for n in self.card_distribution]
        random.shuffle(self.deck)

        self._playing = False
        self._game_over = False
        self._rainbow_game = False  # True if using rainbow (multicolor) cards.

        # table is a dict of lists of cards, indexed by color. 
        self.table = defaultdict(list)

        self.discards = list()   # list of Cards

        # last_round set to 0 when deck is empty and incremented each turn
        # when last_round == num players, the game is over.
        self.last_round = None

    def in_game(self, nick):
        '''Return True is nick is in the game, False otherwise.'''
        return nick in self._players.keys()

    def player_turn(self):
        '''REturn the nick of the player whose turn it is.'''
        return self.turn_order[0]

    def turn(self):
        '''Tell the players whos turn it is.'''
        if not self.turn_order:
            return gr('The game has yet to start. No turns yet.')
        else:
            return gr('It is %s\'s turn to play.' % self.turn_order[0])

    def turns(self):
        '''Tell the players whos turn it is.'''
        if not self.turn_order:
            return gr('Turn order not decided yet; the game has not started.')
        else:
            return gr('Upcoming turns and turn order: %s' % ', '.join(self.turn_order))

    def has_started(self):
        return self._playing

    def game_over(self):
        return self._game_over

    def players(self):
        '''return a list of player ids in the game.'''
        return self._players.keys()

    def discard_card(self, nick, X):
        '''Discard the card with ID X.'''
        retVal = gr()
        if not self._in_game_is_turn(nick, retVal):
            return retVal
        
        i = self._players[nick].card_index(X)
        if i is None:
            retVal.private[nick].append('You tried to discard card %s, oops.' % X)
            retVal.private[nick].append('Card must be one of %s' %
                        ', '.join(sorted([c.mark for x in self._players[nick].hand])))
            return retVal
            
        c = self._players[nick].hand.pop(i)
        if len(self.deck):
            self._players[nick].add_card(self.deck.pop(0))
        else:
            self.last_round = self.last_round + 1 if self.last_round is not None else 1

        retVal.public.append('%s has discarded %s' % (nick, str(c)))
        self.discards.append(c)
        self._flip(self.notes, self.notes_down, self.notes_up)
        self.turn_order.append(self.turn_order.pop(0))

        retVal.merge(self.get_table())

        # tell the next player it is their turn.
        retVal.private[self.turn_order[0]].append('It is your turn in Hanabi.')

        if self._is_game_over():
            retVal.merge(self._end_game())

        return retVal

    def play_card(self, nick, X):
        '''Have player "nick" play card X from his/her hand. "X" is the 
        card ID, e.g. A, B, C, ... N. The output is for group
        consumption.'''
        retVal = gr()
        if not self._in_game_is_turn(nick, retVal):
            return retVal

        i = self._players[nick].card_index(X)
        if i is None:
            retVal.private[nick].append('You tried to play card %s, oops.' % X)
            retVal.private[nick].append('Card must be one of %s' %
                        ', '.join(sorted([c.mark for c in self._players[nick].hand])))
            return retVal

        c = self._players[nick].hand.pop(i)
        if self._is_valid_play(c):
            self.table[c.color].append(c)
            retVal.public.append('%s successfully added %s to the %s group.' %
                       (nick, str(c), c.color))
            if len(self.table[c.color]) == 5:
                retVal.public.append('Bonus for finishing %s group: one note token '
                           'flipped up!' % c.color)
                self._flip(self.notes, self.notes_down, self.notes_up)
        else:
            retVal.public.append('%s guessed wrong with %s! One storm token '
                          'flipped up!' % (nick, str(c)))
            self._flip(self.storms, self.storms_down, self.storms_up)
            self.discards.insert(0, c)

        if len(self.deck):
            self._players[nick].add_card(self.deck.pop(0))
            retVal.public.append('%s drew a new card from the deck into his or her hand.' % nick)
        else:
            self.last_round = self.last_round + 1 if self.last_round is not None else 1

        self.turn_order.append(self.turn_order.pop(0))
        retVal.merge(self.get_table())

        # tell the next player it is their turn.
        retVal.private[self.turn_order[0]].append('It is your turn in Hanabi.')

        if self._is_game_over():
            retVal.merge(self._end_game())

        return retVal

    def hint_player(self, nick, player, hint):
        '''
            hint_player: hint another player about thier hand.

            nick: who is hinting
            player: the hintee
            hint: can be one of: 
                string: a valid color
                int: a valid number (int)

            hint_player validates input.
        '''
        retVal = gr()
        if not self._in_game_is_turn(nick, retVal):
            return retVal
        
        if nick == player:
            retVal.private[nick].append('You really want to give a hint to yourself? Too bad '
                        'no information leak here.')
            return retVal

        try:
            hint = int(hint)
        except ValueError:
            try: 
                hint = str(hint)
            except ValueError:
                retVal.private[nick].append('The hint command must be a string (color) or '
                            'an integer (card number). Valid colors are %s '
                            ' or the first charecter  of the word (all case '
                            'insensitive.' % ', '.join(Game.colors))
                return retVal

        if not player in self._players.keys():
            retVal.private[nick].append('player %s is not in the game.' % player)
            return retVal

        if isinstance(hint, str):
            hint = hint.lower()
            if not hint in Game.colors or (
                    len(hint) == 1 and not hint in [c[0] for c in Game.colors]):
                retVal.public.append('Invalid hint given by %s, still their turn.' % nick)
                retVal.private[nick].append('%s is not a valid color. Valid colors are %s.' %
                        (hint, ', '.join(Game.colors)))
                return retVal

            # convert "?" into full color string.
            if len(hint) == 1:
                hint = [c for c in Game.colors if c[0] == hint][0]

        elif isinstance(hint, int) and not 0 < hint < 6:
            retVal.private[nick].append('numbers must be between 1 and 5 inclusive.')
            return retVal

        # valid hint command, do the action.
        if not self.notes_up in self.notes:
            retVal.public.append('Oh no! %s gave a hint when all notes were turned '
                       'over. ' % nick)
            retVal.public.append('So, ya know, just disregard anything they said.')
            return retVal

        cards = self._get_cards(player, hint)

        if not len(cards):
            retVal.public.append('Looks like %s is as deceiving as a low down dirty '
                       '... deceiver. They gave a hint that does not '
                       'match anything in %s\'s hand!' % (nick, player))
            return retVal

        plural = 's ' if len(cards) > 1 else ' '
        is_are = 'are ' if len(cards) > 1 else 'is '
        a = 'a ' if isinstance(hint, int) else ''
        retVal.public.append('======== %s has given %s a hint: your card%s%s %s%s%s' % (
                   (nick, player, plural, ', '.join([c.mark for c in cards]), is_are, 
                    a, str(hint))))
        self.turn_order.append(self.turn_order.pop(0))
        self._flip(self.notes, self.notes_up, self.notes_down)

        retVal.merge(self.get_table())

        # tell the next player it is their turn.
        retVal.private[self.turn_order[0]].append('It is your turn in Hanabi.')

        return retVal

    def swap_cards(self, nick, A, B):
        '''In nick's hand, swap cards A and B.'''
        retVal = gr()
        if not nick in self._players.keys():
            retVal.private[nick].append('You are not in the game.')
            return retVal

        retVal.merge(self._players[nick].swap_cards(A, B))
        retVal.merge(self.get_hands(nick))
        return retVal

    def sort_cards(self, nick):
        '''In nick's hand, sort cards to "original" A-E order.'''
        retVal = gr()
        if not nick in self._players.keys():
            retVal.private[nick].append('You are not in game %s.')
            return retVal

        retVal.merge(self._players[nick].sort_cards())
        retVal.merge(self.get_hands(nick))
        return retVal

    def move_card(self, nick, A, i):
        '''In nick's hand, move card A to slot i.'''
        retVal = gr()
        if not nick in self._players.keys():
            retVal.private[nick].append('You are not in game %s.')
            return retVal

        retVal.merge(self._players[nick].move_card(A, i))
        retVal.merge(self.get_hands(nick))
        return retVal

    def get_hands(self, nick):
        retVal = gr()
        hands = []
        for p in self._players.values():
            if p.name != nick:
                hands.append(p.get_hand())
            else:
                hands.append(p.get_hand(hidden=True))
        
        # Now let's all join hands...
        retVal.private[nick].append('Current hands: %s' % ', '.join(hands))
        return retVal

    def get_discard_pile(self, nick):
        retVal = gr()
        if not len(self.discards):
            retVal.private[nick].append('There are no cards in the discard pile.')
            return retVal

        retVal.private[nick].append('Discards: %s' % ', '.join([c.front() for c in self.discards]))
        return retVal

    def get_table(self):
        ret = gr()
        # GTL - this could be done in a confusing list comprehension.
        cardstrs = list()
        for cardstack in self.table.values():
            if len(cardstack):
                cardstrs.append(''.join([c.front() for c in cardstack]))

        if not cardstrs:
            ret.public.append('Table: empty')
        else:
            ret.public.append('Table: %s' % ', '.join(cardstrs))

        ret.public.append('Notes: %s, Storms: %s, %d cards remaining.' %
                         (''.join(self.notes), ''.join(self.storms), len(self.deck)))

        if len(self.discards):
            ret.public.append('Discard pile: %s. (size is %d)' %
                             (', '.join([c.front() for c in self.discards]), len(self.discards)))

        ret.merge(self.turn())

        for p in self._players:
            ret.merge(self.get_hands(p))

        return ret

    def add_player(self, nick):
        if self._playing:
            return gr(private={nick:'Game already started.'})

        retVal = gr()
        if len(self._players) >= self.max_players:
            retVal.private[nick].append('Max players already in the game.')
        else:
            if nick in self._players.keys():
                retVal.private[nick].append('You are already in the game.')
            else: 
                self._players[nick] = Player(nick)
                retVal.public.append('%s has joined the game.' % nick)
                if len(self._players) > 1:
                    retVal.public.append('The game has enough players and can be started '
                               'with the start command !start.')

        return retVal

    def remove_player(self, nick):
        if not nick in self._players.keys():
            return gr(private={nick: 'You are not in the game. You cannot be removed from a game you are not in.'})

        retVal = gr()
        retVal.public.append('Removing %s from the game.' % nick)
        retVal.private[nick].append('You\'ve been removed from the game.')
        if self._players[nick].hand:
            retVal.public.append('Putting %s\'s cards back in the deck and reshuffling.' % nick)
            self.deck += self._players[nick].hand
            random.shuffle(self.deck)

        del self._players[nick]

        if len(self._players) < 2:
            retVal.public.append('Stopping the game as there are fewer than two people left in '
                       'the game.')
            self._playing = False
            self._game_over = True

        elif len(self._players) < 4:
            retVal.public.append('Now that there are fewer than four players, everyone gets '
                       'another card. Adding card to each player\s hand.')
            for p in self._players.values():
                if len(self.deck):
                    p.add_card(self.deck.pop(0))

        if self._playing:
            if nick == self.turn_order[0]:
                retVal.public.append('It is now %s\'s turn.' % self.turn_order[1])
       
            del self.turn_order[0]

        return retVal

    def start_game(self, nick, opts=None):
        '''Start an existing game. Will fail if called by someone not in the game
        or if there are not enough players.'''
        retVal = gr()
        if not nick in self._players.keys():
            retVal.private[nick].append('You are not in the game.')
            return retVal

        if self._playing:
            retVal.private[nick].append('The game has already begun.')
            return retVal

        if opts:
            for opt, val in opts.iteritems():
                # only one valid option for now.
                if opt == 'rainbow':
                    self._rainbow_game = True
                    retVal.public.append('Adding rainbow cards to the deck')
                    Game.colors.append('rainbow')
                    self.deck += [Card('rainbow', i) for i in xrange(1,6)]
                    random.shuffle(self.deck)
                else:
                    retVal.public.append('Invalid option to start command: %s' % opt)
                    retVal.public.append('Game not started.')
                    return retVal

        if len(self._players) > 1:
            self._playing = True
            retVal.public.append('The Hanabi game has started!')
            self.turn_order = random.sample(self._players.keys(), len(self._players))
        else:
            retVal.public.append('There are not enough players in the game, not starting.')
            return retVal
       
        card_count = 5 if len(self._players) < 4 else 4
        for player in self._players.values():
            for c in self.deck[:card_count]:
                player.add_card(c)

            self.deck = self.deck[card_count:]

        retVal.merge(self.get_table())
        return retVal

    #
    # "private" methods below
    #
    def _get_cards(self, player, hint):
        '''Figure out which cards the hint is referring to and return the list
        of indexes that match the hint. Hint can be an int (1-5) or a string (color).'''
        return [c for c in self._players[player].hand if c.number == hint or c.color == hint]

    def _flip(self, tokens, A, B):
        '''flip the first non A char token to the B token char.'''
        for i in xrange(len(tokens)):
            if tokens[i] == A:
                tokens[i] = B
                return

    def _is_game_over(self):
        '''Return True if an end game condition is true.'''
        if self.last_round is not None and self.last_round == len(self._players):
            return True
        elif self._rainbow_game and 30 == sum([len(cs) for cs in self.table.values()]):
            return True
        elif not self._rainbow_game and 25 == sum([len(cs) for cs in self.table.values()]):
            return True
        elif not self.storms_down in self.storms:
            return True
        else:
            return False

    def _end_game(self):
        score = sum([len(cs) for cs in self.table.values()])
        self._game_over = True
        self._playing = False
        pub = ['-------------------------']
        pub.append('The game is over. Final score is %d.' % score)
        if 0 <= score <= 5:
            pub.append('Oh dear! The crowd booed.')
        elif 6 <= score <= 10:
            pub.append('Poor! Hardly any applause.')
        elif 11 <= score <= 15:
            pub.append('OK! The audience has seen better.')
        elif 16 <= score <= 20:
            pub.append('Good! The audience is pleased!')
        elif 21 <= score <= 24:
            pub.append('Very good! The audience is enthusiastic!')
        elif score == 25:
            if not self._rainbow_game:
                pub.append('Congratulations! It\'s a perfect game! 25 points!')
            else:
                pub.append('Awesome Job!')
        elif 25 <= score <= 29:    # can happen with rainbow cards
            pub.append('Unbelivable! Well done! The audience is amazed!')
        elif score == 30:
            pub.append('Well, aren\'t you all amazing? A perfect score! The audience\'s brains have melted under the onslaught of beauty!')
        else:
            pub.append('Hmm. score should only be in range 0 to 25 (or 30 w/rainbow cards). Somthing is amiss. Might as well play again...')

        pub += ['-------------------------']
        return gr(pub)

    def _is_valid_play(self, c):
        if not len(self.table[c.color]):
            if c.number == 1:
                return True
            else:
                return False
        else:
            # if card is one greater than last number in color group
            if self.table[c.color][-1].number + 1 == c.number:
                return True
            else:
                return False

    def _in_game_is_turn(self, nick, response):
        '''Return True if the player is in the game and is his/her turn
        else return False.'''
        if not nick in self._players.keys():
            response.private[nick].append('You are not in game.')
            return False
        elif not self._playing:
            response.private[nick].append('The game has not yet started')
            return False
        elif self.turn_order[0] != nick:
            response.private[nick].append('It is not your turn. It is %s\'s turn.' % self.turn_order[0])
            return False

        return True

if __name__ == "__main__":
    import doctest
    doctest.testmod()
