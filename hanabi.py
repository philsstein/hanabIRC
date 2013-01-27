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
            tells a another player about their hand or
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
    >>> str(p)
    'OLIVE: ??????????'
    >>> p.get_hand(hidden=True)
    'OLIVE: ??????????'
    >>> p.get_hand(hidden=False)
    'OLIVE: r[1]r[1]r[2]r[3]r[4]b[1]b[1]b[2]b[3]b[4]'
    >>> p.move_card(2, 3)
    ['OLIVE moved card from slot 2 to slot 3']
    >>> p.get_hand(hidden=False)
    'OLIVE: r[1]r[2]r[1]r[3]r[4]b[1]b[1]b[2]b[3]b[4]'
    '''
    def __init__(self, name, hand, markup):
        self.name = str(name)
        self.hand = hand
        self.markup = markup

    def move_card(self, A, B):
        '''move a card within a hand. output is for the group.'''
        val = self.hand.pop(A-1)
        self.hand.insert(B-1, val)
        return ['%s moved card from slot %d to slot %d' %
                (self.markup.bold(self.name), A, B)]

    def get_hand(self, hidden=False):
        '''return the hand as a string.'''
        if not hidden:
            return '%s: %s' % (self.markup.bold(self.name),
                               ''.join([str(c) for c in self.hand]))
        else:
            return str(self)

    def __str__(self):
            return '%s: %s' % (self.markup.bold(self.name),
                               ''.join(['?' for c in self.hand]))


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
        self.players = {}
        self.max_players = 5
        self.name = name
        self.markup = markup
        self.notes = ['w' for i in range(8)]
        self.storms = ['O' for i in range(3)]
        # The deck is Cards with color and count distributions shown, shuffled.
        colors = [markup.RED, markup.WHITE, markup.BLUE, markup.GREEN,
                  markup.YELLOW]
        self.deck = [Card(c, n, self.markup) for c in colors
                     for n in [1, 1, 1, 2, 2, 2, 3, 3, 4, 4, 5]]
        random.shuffle(self.deck)
        self._playing = False

        # table is a dict of lists of cards, indexed by color or use.
        self.table = {}
        for c in colors:
            self.table[c] = list()     # list of cards.

        self.discards = list()     # list of Cards

    def in_game(self, nick):
        return nick in self.players

    def _flip(self, tokens, A, B):
        '''flipthe first non A char token to the B token char. Return True
        if no tokens found, False otherwise.'''
        for i in xrange(len(tokens)):
            if tokens[i] == A:
                tokens[i] = B
                return False

        return True

    def _end_game(self):
        return (['The game is over.'],[])

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

    def play_card(self, nick, i):
        '''Have player "nick" play card in slot N from his/her hand.
        "i" is indexed by 1 (slot number) and must be between 1 and 5,
        The output is for group consumption.'''
        pub, priv = [], []
        if not nick in self.players:
            return priv.append('You are not in game %s.' % self.markup.bold(self.name))

        c = self.players[nick].hand.pop(i-1)
        retVal = []
        end_game = False
        if self._is_valid_play(c):
            self.table[c.color].append(c)
            self.table[c.color].sort()   # GTL this is not really needed.
            pub.append('%s successfully added %s to the %s group.' %
                          (nick, str(c), c.color))
        else:
            pub.append('%s guessed wrong with %s! One storm token '
                          'flipped!' % (nick, str(c)))
            end_game = self._flip(self.storms, 'O', 'X')
            self.discards.append(c)

        if not len(self.deck) or end_game:
            a, b = self._end_game()
            pub += a
            priv += b
        else:
            pub.append('%s drew a new card from the deck.' % nick)
            self.players[nick].hand.append(self.deck.pop())

        return (pub, priv)

    def move_card(self, nick, A, B):
        '''In nick's hand, move card from A to B slot. Assumes
        input is valid: 1 <= A,B <= 5. So caller should cleanse input.'''
        pub, priv = [], []
        if not nick in self.players:
            priv.append('You are not in game %s.' % self.markup.bold(self.name))

        a, b =  self.players[nick].move_card(A, B)
        pub += a
        priv += b
        return (pub, priv)

    def get_status(self, nick, show_all=False):
        '''Return game status for player, masking that player's cards.'''
        pub = [' --- Game: %s ---' % self.markup.bold(self.name)]
        hands = []
        for p in self.players.values():
            if show_all:
                hands.append(p.get_hand())
            else:
                if p.name != nick:
                    hands.append(p.get_hand())
                else:
                    hands.append(p.get_hand(hidden=True))

        pub.append(', '.join(hands))

        # GTL - this could be done in a confusing list comprehension.
        cardstrs = list()
        for cardstack in self.table.values():
            if len(cardstack):
                cardstrs.append(''.join(str(c) for c in cardstack))

        if not cardstrs:
            pub.append('Table: empty')
        else:
            pub.append('Table: %s' % ', '.join(cardstrs))

        pub.append('Notes: %s, Storms: %s, %d cards remaining.' %
                      (''.join(self.notes), ''.join(self.storms),
                       len(self.deck)))
        if len(self.discards):
            pub.append('Top discard: %s. (size is %d)' %
                          (str(self.discards[-1]), len(self.discards)))

        return (pub,[])

    def show_game_state(self):
        '''Show the entire game status - only for
        debugging/super user/non-players.'''
        pub, priv = [], []
        if len(self.players):
            # we just show the status of frst player w/show_all=True
            a, b = self.get_status(
                self.players[self.players.keys()[0]].name, show_all=True)
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
        if len(self.players) >= self.max_players:
            priv.append('max players already in game %s. You can start'
                          ' another with !new [name]' % self.name)
        else:
            if nick in self.players:
                priv.append('You are already in game %s' % self.name)
            else:
                hand = self.deck[:5]
                self.deck = self.deck[5:]
                self.players[nick] = Player(nick, hand, self.markup)
                pub.append('%s has joined game %s' %
                           (nick, self.markup.bold(self.name)))

        return (pub, priv)

    def remove_player(self, nick):
        if not nick in self.players:
            return ([],['You are not in game %s. You cannot be removed from a game you'
                      ' are not in.' % self.markup.bold(self.name)])

        pub, priv = [], []
        pub.append('Removing %s from game %s' % (nick, self.name))
        priv.append('You\'ve been removed from game %s.' % self.name)
        pub.append('Putting %s\'s cards back in the'
                      ' deck and reshuffling.' % nick)
        self.deck += self.players[nick].hand
        random.shuffle(self.deck)
        self.players = {name: p for name, p in self.players.iteritems() if name != nick}

        return (pub, priv)

    def start_game(self):
        pub, priv = [], []
        if len(self.players) > 1:
            self._playing = True
            pub.append('Game %s started!' % self.markup.bold(self.name))
        else:
            priv.append('There are not enough players in the game, not starting.')

        return (pub, priv)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
