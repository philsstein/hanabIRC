

class text_markup_exception(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class text_markup_base(object):
    '''Abstract bolding and colorizing text. Base class does no markup. This 
    is way overengineered...'''

    # supported colors
    RED = 'red'
    WHITE = 'white'
    BLUE = 'blue'
    GREEN = 'green'
    YELLOW = 'yellow'
    BLACK = 'black'
    RAINBOW = 'rainbow'    # special hanabi color, hacky.

    Colors = [RED, WHITE, BLUE, GREEN, YELLOW, RAINBOW]

    # supported markup
    BOLD = 'bold'
    UNDERLINE = 'underline' 

    Markups = [BOLD, UNDERLINE]

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

    def underline(self, text):
        return self.markup(text, text_markup_base.UNDERLINE)

class irc_markup(text_markup_base):
    '''
    mIRC specific markup encodings.
    See ascii_markup for usage examples.
    '''
    # here are complete? color and control codes
    # for mIRC. This si just for reference. We
    # only support the hanabi colors for now.
    # enum ColorCode {
    #     White           =   0,   /**< White */
    #     Black           =   1,   /**< Black */
    #     DarkBlue        =   2,   /**< Dark blue */
    #     DarkGreen       =   3,   /**< Dark green */
    #     Red         =   4,   /**< Red */
    #     DarkRed         =   5,   /**< Dark red */
    #     DarkViolet      =   6,   /**< Dark violet */
    #     Orange          =   7,   /**< Orange */
    #     Yellow          =   8,   /**< Yellow */
    #     LightGreen      =   9,   /**< Light green */
    #     Cyan            =  10,   /**< Cornflower blue */
    #     LightCyan       =  11,   /**< Light blue */
    #     Blue            =  12,   /**< Blue */
    #     Violet          =  13,   /**< Violet */
    #     DarkGray            =  14,   /**< Dark gray */
    #     LightGray       =  15   /**< Light gray */
    # };
    # 
    # enum ControlCode {
    #     Bold            = 0x02,     /**< Bold */
    #     Color           = 0x03,     /**< Color */
    #     Italic          = 0x09,     /**< Italic */
    #     StrikeThrough           = 0x13,     /**< Strike-Through */
    #     Reset           = 0x0f,     /**< Reset */
    #     Underline       = 0x15,     /**< Underline */
    #     Underline2      = 0x1f,     /**< Underline */
    #     Reverse         = 0x16      /**< Reverse */
    # }; 
    # from mIRC color codes
    _colormap = {
        text_markup_base.WHITE: 0,
        text_markup_base.BLUE: 11,
        text_markup_base.GREEN: 9,
        text_markup_base.RED: 4,
        text_markup_base.YELLOW: 8,
        text_markup_base.BLACK: 1,
        text_markup_base.RAINBOW: 0
    }

    def __init__(self):
        text_markup_base.__init__(self)
        self.bg_color = irc_markup._colormap[text_markup_base.BLACK]

    def markup(self, text, markup):
        text_markup_base.markup(self, text, markup)
        if markup == text_markup_base.BOLD:
            return '\x02%s\x02' % text
        elif markup == text_markup_base.UNDERLINE:
            return '\x1f%s\x1f' % text
        else:
            return text

    def color(self, text, color):
        text_markup_base.color(self, text, color)
        if color == text_markup_base.RAINBOW:
            retVal = ''
            for i, c in enumerate(text):
                retVal += self.color(c, text_markup_base.Colors[i % (len(text_markup_base.Colors)-1)])

            return retVal
        else:
            return '\x03%02d,%02d%s\x03' % (irc_markup._colormap[color],
                                            irc_markup._colormap[text_markup_base.BLACK], text)


class xterm_markup(text_markup_base):
    '''
    markup for xterms.
    '''
    _colormap = {
        text_markup_base.WHITE: 37,
        text_markup_base.BLUE: 34,
        text_markup_base.GREEN: 32,
        text_markup_base.RED: 31,
        text_markup_base.YELLOW: 33,
        text_markup_base.RAINBOW: 37
    }

    def __init__(self):
        text_markup_base.__init__(self)

    def markup(self, text, markup):
        text_markup_base.markup(self, text, markup)
        # GTL - I don't know how to BOLD without knowing the current fg color.
        return text

    def color(self, text, color):
        text_markup_base.color(self, text, color)
        if color == text_markup_base.RAINBOW:
            retVal = ''
            for i, c in enumerate(text):
                retVal += self.color(c, text_markup_base.Colors[i % (len(text_markup_base.Colors)-1)])

            return retVal
        else:
            return '\033[%d;1m%s\033[0m' % (xterm_markup._colormap[color], text)


class ascii_markup(text_markup_base):
    '''
    pseudo markup for ascii terminals.

    pydoctest code/sample:
        >>> from text_markup import ascii_markup as markup
        >>> m = markup()
        >>> m.color('hello', m.RED)
        'Rhello'
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
        text_markup_base.WHITE: 'W',
        text_markup_base.BLUE: 'B',
        text_markup_base.GREEN: 'G',
        text_markup_base.RED: 'R',
        text_markup_base.YELLOW: 'Y',
        text_markup_base.RAINBOW: 'RNBW'
    }

    def __init__(self):
        text_markup_base.__init__(self)

    def bold(self, text):
        return self.markup(text, self.BOLD)

    def markup(self, text, markup):
        text_markup_base.markup(self, text, markup)
        return text.upper()

    def color(self, text, color):
        text_markup_base.color(self, text, color)
        return '%s%s' % (ascii_markup._colormap[color], text)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
