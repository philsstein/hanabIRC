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
    '''

    def __init__(self, name, hand, markup):
        self.name = str(name)
        self.hand = hand
        self.markup = markup

    def get_hand(self, hidden=False):
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

        Most functions return a list of strings suitable to outputting
        to a console or IRC channel, etc.

        See below for extended usage sample.

        Example:
        >>> from text_markup import ascii_markup
        >>> g = Game('foobar', ascii_markup())
        >>> g.start_game()
        ['There are not enough players in the game, not starting.']
        >>> g.add_player('Olive')
        ['Olive has joined game foobar']
        >>> g.add_player('Maisie')
        ['Maisie has joined game foobar']
        >>> g.start_game()
        ['Game foobar started!']
        >>> for l in g.get_status('Olive'): print l     # doctest: +ELLIPSIS
         --- Game: FOOBAR ---
        OLIVE: ?????, MAISIE: ...
        Notes: wwwwwwww, Storms: ___
        45 cards remaining
        >>> for l in g.get_status('Maisie'): print l    # doctest: +ELLIPSIS
         --- Game: FOOBAR ---
        OLIVE: ..., MAISIE: ?????
        Notes: wwwwwwww, Storms: ___
        45 cards remaining

        In this example the "..." would be the random hand of the player
        listed.
    '''
    def __init__(self, name, markup):
        '''
        name: the name of the game as an ID.
        text_markup: a class for marking up the the return game state text.
            Enables bolding, colorizing, etc text that is returned. Useful
            for abstracting markup to support mulitple bolding and colorizing
            contexts, like IRC and xterms.
        '''
        self.players = []
        self.max_players = 5
        self.name = name
        self.markup = markup
        self.notes = ['w' for i in range(8)]
        self.storms = ['_' for i in range(3)]
        # The deck is Cards with color and count distributions shown, shuffled.
        colors = [markup.RED, markup.WHITE, markup.BLUE, markup.GREEN,
                  markup.YELLOW]
        self.deck = [Card(c, n, self.markup) for c in colors
                     for n in [1, 1, 1, 2, 2, 2, 3, 3, 4, 4, 5]]
        random.shuffle(self.deck)

    def in_game(self, nick):
        for p in self.players:
            if p.name == nick:
                return True

        return False

    def get_status(self, nick, show_all=False):
        '''Return game status for player, masking that player's cards.'''
        retVal = [' --- Game: %s ---' % self.markup.markup(self.name,
                                                           self.markup.BOLD)]
        players = []
        for p in self.players:
            if show_all:
                players.append(p.get_hand())
            else:
                if p.name != nick:
                    players.append(p.get_hand())
                else:
                    players.append(p.get_hand(hidden=True))

        retVal.append('%s' % ', '.join(players))
        retVal.append('Notes: %s, Storms: %s' % (''.join(self.notes),
                                                 ''.join(self.storms)))
        retVal.append('%d cards remaining' % len(self.deck))

        return retVal

    def show_game_state(self):
        '''Show the entire game status - only for
        debugging/super user/non-players.'''
        retVal = list()
        if len(self.players):
            retVal += self.get_status(self.players[0].name, show_all=True)
        else:
            retVal.append(' --- Game %s is waiting for players to join --- ' %
                          self.markup.bold(self.name))

        retVal.append('Deck: %s' % ''.join([str(c) for c in self.deck]))

        return retVal

    def add_player(self, nick):
        retVal = list()
        if len(self.players) >= self.max_players:
            retVal.append('max players already in game %s. You can start'
                          'another with !new [name]' % self.name)
        else:
            for p in self.players:
                if p.name == nick:
                    retVal.append('You are already in game %s' % self.name)
                    break  # do not do else clause
            else:
                hand = self.deck[:5]
                self.deck = self.deck[5:]
                self.players.append(Player(nick, hand, self.markup))
                retVal.append('%s has joined game %s' % (nick, self.name))

        return retVal

    def remove_player(self, nick):
        retVal = []
        for p in self.players:
            if p.name == nick:
                retVal.append('Putting %s\'s cards back in the'
                              'deck and reshuffling.' % (p.name))
                self.deck += p.hand
                random.shuffle(self.deck)
                retVal.append('Removing %s from game %s' % (p.name, self.name))
                self.players = [p for p in self.players if p.name != nick]
                break

        return retVal

    def start_game(self):
        if len(self.players) > 1:
            self.playing = True
        else:
            return ['There are not enough players in the game, not starting.']

        return ['Game %s started!' % self.name]

if __name__ == "__main__":
    import doctest
    doctest.testmod()
