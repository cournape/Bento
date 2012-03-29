import sys

import six

class Peeker(object):
    """Generator to enable "peeking" the next item

    Parameters
    ----------
    it : iterator
        iterator which we one to peek in
    dummy :
        if not None, will be returned by peek if the iterator is empty

    Example
    -------
    >>> a = [1, 2, 3, 4]
    >>> peeker = Peeker(a)
    >>> for i in peeker:
    >>>     try:
    >>>         next = peeker.peek()
    >>>         print "Next to %d is %d" % (i, next)
    >>>     except StopIteration:
    >>>         print "End of stream", i
    """
    def __init__(self, it, dummy=None):
        self._it = iter(it)
        self._cache = None
        if dummy is None:
            self.peek = self._peek_no_dummy
        else:
            self.peek = self._peek_dummy
        self._dummy = dummy

    def __next__(self):
        return self.next()

    def next(self):
        if self._cache:
            i = self._cache
            self._cache = None
            return i
        else:
            return six.advance_iterator(self._it)
        #self._cache = None
        #return i

    def _peek_dummy(self):
        if self._cache:
            return self._cache
        else:
            try:
                i = six.advance_iterator(self._it)
            except StopIteration:
                return self._dummy
            self._cache = i
            return i

    def _peek_no_dummy(self):
        if self._cache:
            return self._cache
        else:
            i = six.advance_iterator(self._it)
            self._cache = i
            return i

    def __iter__(self):
        return self

class BackwardGenerator(object):
    def __init__(self, gen):
        self._gen = gen
        self._cache = []
        self._previous = None

    def next(self):
        c = six.advance_iterator(self._gen)
        if len(self._cache) == 2:
            old, new = self._cache
            self._cache = [new]
        self._cache.append(c)
        return c

    def __next__(self):
        return self.next()

    def previous(self):
        if len(self._cache) < 2:
            raise ValueError()
        return self._cache[0]

    def __iter__(self):
        return self

def print_tokens_simple(lexer):
    while True:
        tok = lexer.token()
        if not tok:
            break
        print(tok)
