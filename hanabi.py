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

log = logging.getLogger(__name__)


class Card(object):
    '''
    Card has a color and a number and uses a markup object instance
    to print the color and number approipriately. The color must be
    supported by the markup instance.

    Example:
    >>> from text_markup import ascii_markup
    >>> a = ascii_markup()
    >>> c = Card(ascii_markup.RED, 4, a)
    >>> str(c)
    'r[4]'
    >>> c = Card('blue', 1, a)
    >>> str(c)
    'b[1]'
    >>> c = Card('purple', 1, a)
    Traceback (most recent call last):
        ...
    text_markup_exception: 'Unknown color: purple'
    '''
    def __init__(self, color, number, markup):
        self.markup = markup
        self.color = color
        self.number = number

        # if color is bad, this will raise an exception.
        self.markup.color('hello', self.color)

    def __str__(self):
        return '%s' % self.markup.color('%d' % self.number, self.color)


class Player(object):
    '''
    Player has a name and a hand and uses a markup instance to print
    player information appropriately.

    If the player themselves is requesting to see the hand, they get
    an opaque hand. If anyone else wants to see it, they see it all.

    Players can modify the order of cards in their own hands as well.

    example:
    >>> from text_markup import ascii_markup
    >>> a = ascii_markup()
    >>> hand=[Card(c, n, a) for c in ['red', 'blue'] for n in [1, 1, 2, 3, 4]]
    >>> p = Player('Olive', hand, a)
    >>> p.get_hand('Olive')
    'OLIVE: ABCDE
    >>> p.get_hand(hidden=True)
    'OLIVE: ??????????'
    >>> p.get_hand(hidden=False)
    'OLIVE: r[1]r[1]r[2]r[3]r[4]b[1]b[1]b[2]b[3]b[4]'
    >>> p.swap_cards(2, 3)
    ['OLIVE moved card from slot 2 to slot 3']
    >>> p.get_hand(hidden=False)
    'OLIVE: r[1]r[2]r[1]r[3]r[4]b[1]b[1]b[2]b[3]b[4]'
    '''
    def __init__(self, name, hand, markup):
        if len(hand) > len(string.uppercase):
            raise Exception('Max hand size exceeded: %d. Max is %s' % (
                len(hand), len(string.uppercase)))

        self.name = str(name)
        self.markup = markup    
        # The player's hand, a list of Cards
        self.hand = hand
        # The posistions of cards in hand, Displayed to the player
        # so they can track cards by position in hand.
        # (support for more than 5 cards though it'll never be used.)
        self.positions = [string.uppercase[i] for i in xrange(len(hand))]

    def sort_cards(self):
        '''resort the card into "orginal" positions.'''
        # confusing and ugly, sorry.
        # sort the zipped arrays by position, i.e. the strings 'A', 'B, etc.
        tmp = zip(self.positions, self.hand)
        tmp.sort(key=lambda x: x[0])        # sort by 'A', 'B', etc.
        pos, hand = zip(*tmp)               # "unzip" the values
        self.positions = list(pos)          # and put them back as lists.
        self.hand = list(hand)

        pub, priv = [], []
        pub.append('%s sorted thier cards.' % self.name)
        return pub, priv

    def swap_cards(self, A, B):
        '''move a card within a hand. output is for the group. A and B
        are 1-based index into the hand.'''
        pub, priv = [], []
        try:
            A = int(A)
            B = int(B)
        except ValueError:
            priv.append('!move args must be integers between 1 and 5.')
            return pub, priv

        if not (0 < A < 6) or not (0 < B < 6):
            priv.append('!move args must be between 1 and 5.')
            return pub, priv

        self.hand[A-1], self.hand[B-1] = self.hand[B-1], self.hand[A-1]
        self.positions[A-1], self.positions[B-1] = self.positions[B-1], self.positions[A-1]
        pub.append('%s swapped cards in slots %d and slot %d' %
                    (self.markup.bold(self.name), A, B))
        return pub, priv

    def add_card(self, card):
        '''Add a card to a player's hand. Use this method and not add to
        player.hand directly. Only call when the player has less than 
        hand limit cards, i.e. soon after calling player.get_card(). The
        card is placed on the rightmost end of the hand, in slot 5.'''
        self.hand.append(card)
        # add the missing position card.
        for p in ['A', 'B', 'C', 'D', 'E']:
            if not p in self.positions:
                self.positions.append(p)
                break

    def get_card(self, i):
        '''Get the card at position i and remove it from the player's
        hand. Hand is 1-based positioning.'''
        self.positions.pop(i-1)
        return self.hand.pop(i-1)

    def get_hand(self, hidden=False):
        '''return the hand as a string.'''
        if not hidden:
            return '%s: %s' % (self.markup.bold(self.name),
                               ''.join([str(c) for c in self.hand]))
        else:
            return '%s: %s' % (self.markup.bold(self.name),
                               ''.join(self.positions))

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
        >>> def display(pub, priv):
        ...     for d in [('public:', pub), ('private:', priv)]:
        ...             print d[0]
        ...             for l in d[1]:
        ...                     print l
        >>> from text_markup import ascii_markup
        >>> g = Game('foobar', ascii_markup())
        >>> g.start_game()
        ['There are not enough players in the game, not starting.']
        >>> g.add_player('Olive')
        ['Olive has joined game foobar']
        >>> g.add_player('Maisie')
        ['Maisie has joined game foobar']
        >>> g.start_game()
        ['Game FOOBAR started!']
        >>> g.in_game('Olive')
        True
        >>> g.in_game('Fred')
        False
        >>> for l in g.get_status('Olive'): print l     # doctest: +ELLIPSIS
         --- Game: FOOBAR ---
        OLIVE: ?????, MAISIE: ...
        Table: empty
        Notes: wwwwwwww, Storms: OOO, 45 cards remaining.
        >>> for l in g.get_status('Maisie'): print l        # doctest: +ELLIPSIS
         --- Game: FOOBAR ---
        OLIVE: ..., MAISIE: ?????
        Table: empty
        Notes: wwwwwwww, Storms: OOO, 45 cards remaining.
    '''
    def __init__(self, name, markup):
        '''
        name: the name of the game as an ID.
        text_markup: a class for marking up the the return game state text.
            Enables bolding, colorizing, etc text that is returned. Useful
            for abstracting markup to support mulitple bolding and colorizing
            contexts, like IRC and xterms.
        '''
        self._players = {}
        # turn_order[0] is always current player's name
        self.turn_order = []
        self.max_players = 5
        self.name = name
        self.markup = markup

        self.notes_up, self.notes_down = ('w', 'b')
        self.notes = [self.notes_up for i in range(8)]
        self.storms_up, self.storms_down = ('X', 'O')
        self.storms = [self.storms_down for i in range(3)]
        
        # The deck is Cards with color and count distributions shown, shuffled.
        self.colors = [markup.RED, markup.WHITE, markup.BLUE, markup.GREEN,
                  markup.YELLOW]
        self.card_distribution = [1, 1, 1, 2, 2, 2, 3, 3, 4, 4, 5]
        self.deck = [Card(c, n, self.markup) for c in self.colors
                     for n in self.card_distribution]

        random.shuffle(self.deck)
        self._playing = False
        self._game_over = False

        # table is a dict of lists of cards, indexed by color or use.
        self.table = {}
        for c in self.colors:
            self.table[c] = list()     # list of cards.

        self.discards = list()     # list of Cards

    def in_game(self, nick):
        '''Return True is nick is in the game, False otherwise.'''
        return nick in self._players.keys()

    def turn(self, nick):
        '''Tell the players whos turn it is.'''
        t = 'N/A' if not self.turn_order else self.turn_order[0]
        return (['It is %s\'s turn to play.' % t], [])

    def has_started(self):
        return self._playing

    def game_over(self):
        return self._game_over

    def players(self):
        '''return a list of player ids in the game.'''
        return self._players.keys()

    def discard_card(self, nick, i):
        '''Discard the card in slot i.'''
        pub, priv = [], []
        if not self._in_game_is_turn(nick, priv):
            return (pub, priv)

        if not (0 < i < 6):
            pub.append(['%s tried to discard card in slot %d, oops.' % (nick, i)])
            priv.append(['card slots must be between 1 and 5 inclusive.'])
            return (pub, priv)
            
        c = self._players[nick].get_card(i)
        pub.append('%s has discarded a %s' % (nick, str(c)))
        self.discards.append(c)
        self._players[nick].add_card(self.deck.pop(0))
        self._flip(self.notes, self.notes_down, self.notes_up)
        self.turn_order.append(self.turn_order.pop(0))
        pub.append('It is now %s\'s turn in game %s.' %
                   (self.turn_order[0], self.markup.bold(self.name)))

        if self._is_game_over():
            self._end_game(pub, priv)

        return (pub, priv)    

    def play_card(self, nick, i):
        '''Have player "nick" play card in slot N from his/her hand.
        "i" is indexed by 1 (slot number) and must be between 1 and 5,
        The output is for group consumption.'''
        pub, priv = [], []
        if not self._in_game_is_turn(nick, priv):
            return (pub, priv)

        c = self._players[nick].get_card(i)
        if self._is_valid_play(c):
            self.table[c.color].append(c)
            pub.append('%s successfully added %s to the %s group.' %
                          (nick, str(c), c.color))
            if len(self.table[c.color]) == 5:
                pub.append('%s for finishing color: one note token flipped!' %
                           self.markup.bold('Bonus'))
                
                self._flip(self.notes, self.notes_down, self.notes_up)
        else:
            pub.append('%s guessed wrong with %s! One storm token '
                          'flipped!' % (nick, str(c)))
            self._flip(self.storms, self.storms_down, self.storms_up)
            self.discards.insert(0, c)

        self._players[nick].add_card(self.deck.pop())
        pub.append('%s drew a new card from the deck into slot 5.' % nick)

        self.turn_order.append(self.turn_order.pop(0))
        pub.append('It is now %s\'s turn in game %s.' %
                   (self.turn_order[0], self.markup.bold(self.name)))

        if self._is_game_over():
            self._end_game(pub, priv)

        return (pub, priv)

    def hint_player(self, nick, other_nick, cmd, slots):
        '''
            hint_player: hint another player about thier hand.

            nick: who is hinting
            other_nick: the hintee
            cmd: can be one of: 
                string: a valid color
                int: a valid number (int)
            slots: a list of card slots.

            hint_player validates input.
        '''
        pub, priv = [], []
        if not self._in_game_is_turn(nick, priv):
            return (pub, priv)

        pub.append('Invalid hint command still %s\'s turn.' % self.turn_order[0])
        if not other_nick in self._players.keys():
            priv.append('player %s is not in the game %s.' % (other_nick, self.name))
            return (pub, priv)

        if not isinstance(slots, list):
            priv.append('I did not understand that hint command.')
            return (pub, priv)

        if isinstance(cmd, str):
            if not cmd in self.colors:
                # color the colors with thier own colors...
                colors = [self.markup.color(c, c) for c in self.colors]
                priv.append('%s is not a valid color. Valid colors are %s.' %
                        (cmd, ', '.join(colors)))
                return (pub, priv)
            else:
                # color the color with its color.
                cmd = self.markup.color(cmd, cmd)
        elif isinstance(cmd, int) and not 0 < cmd < 6:
            priv.append('numbers must be between 1 and 5 inclusive.')
            return (pub, priv)

        for s in slots:
            if not 0 < s < 6:
                priv.append('Slots must be between 1 and 5 inclusive.')
                return (pub, priv)

        # TODO: Do we want to actually validate the hint command?
        # if a lie, tell everyone that 'nick' is a dirty-low down
        # deceiver. 

        # valid hint command, do the action.
        pub = []
        if not self.notes_up in self.notes:
            pub.append('Oh no! %s gave a hint when all notes were black '
                       'side down. ' % nick)
            pub.append('Shame on them!')

        plural = 's' if len(slots) > 1 else ''
        pub.append('%s: your hand contains a %s card in slot%s %s' %
               (other_nick, str(cmd), plural,
                ', '.join([str(s) for s in slots])))
        self.turn_order.append(self.turn_order.pop(0))
        pub.append('It is now %s\'s turn in game %s.' %
                   (self.turn_order[0], self.markup.bold(self.name)))

        self._flip(self.notes, self.notes_up, self.notes_down)

        return (pub, priv)

    def swap_cards(self, nick, A, B):
        '''In nick's hand, move card from A to B slot.'''
        pub, priv = [], []
        if not nick in self._players.keys():
            priv.append('You are not in game %s.' % self.markup.bold(self.name))
            return (pub, priv)

        pub, priv = self._players[nick].swap_cards(A, B)
        return (pub, priv)

    def sort_cards(self, nick):
        '''In nick's hand, sort cards to "original" A-E order.'''
        pub, priv = [], []
        if not nick in self._players.keys():
            priv.append('You are not in game %s.' % self.markup.bold(self.name))
            return (pub, priv)

        pub, priv = self._players[nick].sort_cards()
        return (pub, priv)

    def get_status(self, nick, show_all=False):
        '''Return game status for player, masking that player's cards.'''
        pub = []
        priv = ['--- Game Status: %s ---' % self.markup.bold(self.name)]
        hands = []
        for p in self._players.values():
            if show_all:
                hands.append(p.get_hand())
            else:
                if p.name != nick:
                    hands.append(p.get_hand())
                else:
                    hands.append(p.get_hand(hidden=True))

        priv.append(', '.join(hands))

        # GTL - this could be done in a confusing list comprehension.
        cardstrs = list()
        for cardstack in self.table.values():
            if len(cardstack):
                cardstrs.append(''.join(str(c) for c in cardstack))

        if not cardstrs:
            priv.append('Table: empty')
        else:
            priv.append('Table: %s' % ', '.join(cardstrs))

        cur_player = self.turn_order[0] if len(self.turn_order) else 'N/A'
        priv.append('Notes: %s, Storms: %s, %d cards remaining.' %
                      (''.join(self.notes), ''.join(self.storms), 
                       len(self.deck)))
        priv.append('Current player: %s' % cur_player)
        if len(self.discards):
            priv.append('Top discard: %s. (size is %d)' %
                          (str(self.discards[-1]), len(self.discards)))

        return (pub, priv)

    def show_game_state(self):
        '''Show the entire game status - only for
        debugging/super user/non-players.'''
        pub, priv = [], []
        if len(self._players):
            # we just show the status of frst player w/show_all=True
            a, b = self.get_status(
                self._players[self._players.keys()[0]].name, show_all=True)
            pub += a
            priv += b
        else:
            priv.append(' --- Game %s is waiting for players to join --- ' %
                          self.markup.bold(self.name))

        priv.append('Deck: %s' % ''.join([str(c) for c in self.deck]))
        priv.append('Discard: %s' % ''.join([str(c) for c in self.discards]))

        return (pub, priv)

    def add_player(self, nick):
        if self._playing:
            return ([],['Game %s already started.' % self.markup.bold(self.name)])

        pub, priv = [], []
        if len(self._players) >= self.max_players:
            priv.append('max players already in game %s. You can start'
                          ' another with !new [name]' % self.name)
        else:
            if nick in self._players.keys():
                priv.append('You are already in game %s' % self.name)
            else:
                hand = self.deck[:5]
                self.deck = self.deck[5:]
                self._players[nick] = Player(nick, hand, self.markup)
                pub.append('%s has joined game %s.' %
                           (nick, self.markup.bold(self.name)))
                if len(self._players) > 1:
                    pub.append('Game %s has enough players and can be started '
                               'with the start command,' % self.markup.bold(self.name))

        return (pub, priv)

    def remove_player(self, nick):
        if not nick in self._players.keys():
            return ([],['You are not in game %s. You cannot be removed from a game you'
                      ' are not in.' % self.markup.bold(self.name)])

        pub, priv = [], []
        pub.append('Removing %s from game %s' % (nick, self.name))
        priv.append('You\'ve been removed from game %s.' % self.name)
        pub.append('Putting %s\'s cards back in the' ' deck and reshuffling.' % nick)
        self.deck += self._players[nick].hand
        random.shuffle(self.deck)
        del self._players[nick]

        if len(self._players) < 2:
            pub.append('Stopping game %s as there are fewer than two people left in '
                       'the game.' % self.markup.bold(self.name))
            self._playing = False
            self._game_over = True

        if self._playing:
            if nick == self.turn_order[0]:
                pub.append('It is now %s\'s turn.' % self.turn_order[1])
       
            del self.turn_order[0]

        return (pub, priv)

    def start_game(self, nick):
        '''Start an existing game. Will fail if called by someone not in the game
        or if there are not enough players.'''
        pub, priv = [], []
        if not nick in self._players.keys():
            priv.append('You are not in game %s.' % self.markup.bold(self.name))
            return (pub, priv)

        if self._playing:
            priv.append('Game %s has already begun.' % self.markup.bold(self.name))
            return (pub, priv)

        if len(self._players) > 1:
            self._playing = True
            pub.append('%s game with game id "%s" has begun!' %
                       (self._rainbow('Hanabi'), self.markup.bold(self.name)))
            self.turn_order = random.sample(self._players.keys(), len(self._players))
        else:
            priv.append('There are not enough players in the game, not starting.')
            return (pub, priv)
        
        pub.append('It is now %s\'s turn in game %s.' %
                   (self.turn_order[0], self.markup.bold(self.name)))
        return (pub, priv)
    #
    # "private" methods below
    #

    def _rainbow(self, s):
        '''Return a string in a rainbox of colors.'''
        ret = ''
        colors = [self.markup.RED, self.markup.WHITE, self.markup.BLUE,
                  self.markup.GREEN, self.markup.YELLOW]
        for i in range(len(s)):
            ret += self.markup.color(s[i], colors[0])
            colors.append(colors.pop(0))

        return ret

    def _flip(self, tokens, A, B):
        '''flip the first non A char token to the B token char.'''
        for i in xrange(len(tokens)):
            if tokens[i] == A:
                tokens[i] = B
                return

    def _is_game_over(self):
        '''Return True if ay end game condition is true.'''
        if not len(self.deck):
            return True
        elif 25 == sum([len(cs) for cs in self.table.values()]):
            return True
        elif not self.storms_down in self.storms:
            return True

    def _end_game(self, pub, priv):
        score = sum([len(cs) for cs in self.table.values()])
        self._game_over = True
        self._playing = False
        pub += ['-------------------------']
        pub.append('Game %s is over. Final score is %d.' %
                   (self.markup.bold(self.name), score))
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
            pub.append('%s! It\'s a perfect game! 25 points!' % self._rainbow('Congratulations'))
        else:
            pub.append('Hmm. score should only be in range 0 to 25. Somthing is amiss. '
                       ' Might as well play again...')

        pub += ['-------------------------']

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

    def _in_game_is_turn(self, nick, priv):
        '''Return True if the player is in the game and is his/her turn
        else return False.'''
        if not nick in self._players.keys():
            priv.append('You are not in game %s.' % self.markup.bold(self.name))
            return False
        elif not self._playing:
            priv.append('The game %s has not yet started' % self.name)
            return False
        elif self.turn_order[0] != nick:
            priv.append('It is not your turn. It is %s\'s turn.' % self.turn_order[0])
            return False

        return True

if __name__ == "__main__":
    import doctest
    doctest.testmod()
