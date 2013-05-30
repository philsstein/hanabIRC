#!/usr/bin/env python 

from collections import defaultdict

class GameResponse(object):
    '''Encapsulates a response from a Game Engine. Contains
    return value (bool), a public string, a a dict of private
    responses, index by player name. If return value is False, 
    the parser should not display the output as there was an 
    internal error.

    >>>
    >>> if GameResponse(retVal=True): 
    ...     print "yes"
    yes
    >>> def OfficalResponse():
    ...     return GameResponse(public='There is no cause for alarm.', 
    ...                         private={'generals': 'We are foobared.', 
    ...                                  'privates': ['suit up', 'the time is now.']}, 
    ...                         retVal=True)
    >>>
    >>> resp = OfficalResponse()
    >>> if resp:
    ...     for message in resp.public:
    ...         print 'Public: %s' % message
    ...     for name, messages in resp.private.iteritems():
    ...             for message in messages:
    ...                 print 'PRIVATE: %s - %s' % (name, message)
    Public: There is no cause for alarm.
    PRIVATE: privates - suit up
    PRIVATE: privates - the time is now.
    PRIVATE: generals - We are foobared.
    >>>
    '''
    def __init__(self, public=None, private=None, retVal=True):
        '''Intialize an instance of GameResponse. public can e a string
        or list of strings. private can be a dict of (str or list of string) 
        indexed by name.'''
        self._retVal = retVal
        self._public = list()
        if public:
            if isinstance(public, (str, unicode)):
                self._public.append(public)
            else:
                self._public += public

        self._private = defaultdict(list)
        if private:
            for k in private.keys():
                if isinstance(private[k], (str, unicode)):
                    self._private[k].append(private[k])
                else:
                    self._private[k] += private[k]

    def merge(self, gr):
        self._retVal = self._retVal and gr._retVal
        self._public += gr.public
        for name in gr.private.keys():
            self.private[name] += gr.private[name]

    def __str__(self):
        r = 'value: %s\n' % self._retVal
        if self._public:
            if isinstance(self._public, (str, unicode)):
                r += ' public: %s\n' % ', '.join(self._public)
            else:
                for l in self._public:
                    r += ' public: %s\n' % l


        for p, ms in self._private.iteritems():
            r += ' %s: %s\n' % (p, ', '.join(ms))

        return r

    def __repr__(self):
        return str(self)

    @property
    def public(self):
        return self._public

    @public.setter
    def public(self, value):
        self._public = value

    @property
    def private(self):
        return self._private

    @private.getter
    def private(self):
        return self._private

    @private.setter
    def private(self, val):
        self._private = val

    def __nonzero__(self):
        return self._retVal

if __name__ == "__main__":
    import doctest
    doctest.testmod()

