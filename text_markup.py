

class text_markup_exception(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class text_markup_base(object):
    '''Abstract bolding and colorizing text. Base class does no markup.'''

    # supported colors
    RED = 'red'
    WHITE = 'white'
    BLUE = 'blue'
    GREEN = 'green'
    YELLOW = 'yellow'

    Colors = [RED, WHITE, BLUE, GREEN, YELLOW]

    # supported markup
    BOLD = 'bold'

    Markups = [BOLD]

    def __init__(self):
        pass

    def markup(self, text, markup):
        '''just check for supported markup. raise exception if not
        supported.'''
        if not markup in text_markup_base.Markups:
            raise text_markup_exception('Unknown markup: %s' % markup)

        return text

    def color(self, text, color):
        '''just check for supported color. raise exception if not supported.'''
        if not color in text_markup_base.Colors:
            raise text_markup_exception('Unknown color: %s' % color)

        return text

    def bold(self, text):
        return self.markup(text, text_markup_base.BOLD)


class irc_markup(text_markup_base):
    '''
    mIRC specific markup encodings.
    See ascii_markup for usage examples.
    '''

    # from mIRC color codes
    _colormap = {
        text_markup_base.WHITE: 0,
        text_markup_base.BLUE: 2,
        text_markup_base.GREEN: 3,
        text_markup_base.RED: 4,
        text_markup_base.YELLOW: 8
    }

    def __init__(self):
        text_markup_base.__init__(self)

    def markup(self, text, markup):
        text_markup_base.markup(self, text, markup)
        # we only do bold for now. Replace with if esif chain when we
        # support more.
        return '\x02%s\x02' % text

    def color(self, text, color):
        text_markup_base.color(self, text, color)
        return '\x03%02d%s\x03' % (irc_markup._colormap[color], text)


class xterm_markup(text_markup_base):
    '''
    markup for xterms.
    '''
    _colormap = {
        text_markup_base.WHITE: 37,
        text_markup_base.BLUE: 34,
        text_markup_base.GREEN: 32,
        text_markup_base.RED: 31,
        text_markup_base.YELLOW: 33
    }

    def __init__(self):
        text_markup_base.__init__(self)

    def markup(self, text, markup):
        text_markup_base.markup(self, text, markup)
        # GTL - I don't know how to BOLD without knowing the current fg color.
        return text

    def color(self, text, color):
        text_markup_base.color(self, text, color)
        return '\033[%d;1m%s\033[0m' % (xterm_markup._colormap[color], text)


class ascii_markup(text_markup_base):
    '''
    pseudo markup for ascii terminals.

    pydoctest code/sample:
        >>> from text_markup import ascii_markup as markup
        >>> m = markup()
        >>> m.color('hello', m.RED)
        'r[hello]'
        >>> m.markup('hello', m.BOLD)
        'HELLO'
        >>> m.color('hello', 'purple')
        Traceback (most recent call last):
            ...
        text_markup_exception: 'Unknown color: purple'
        >>> m.markup('hello', 'underlined')
        Traceback (most recent call last):
            ...
        text_markup_exception: 'Unknown markup: underlined'
        '''
    _colormap = {
        text_markup_base.WHITE: 'w',
        text_markup_base.BLUE: 'b',
        text_markup_base.GREEN: 'g',
        text_markup_base.RED: 'r',
        text_markup_base.YELLOW: 'y'
    }

    def __init__(self):
        text_markup_base.__init__(self)

    def markup(self, text, markup):
        text_markup_base.markup(self, text, markup)
        return text.upper()

    def color(self, text, color):
        text_markup_base.color(self, text, color)
        return '%s[%s]' % (ascii_markup._colormap[color], text)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
