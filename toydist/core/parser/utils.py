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

    def next(self):
        if self._cache:
            i = self._cache
            self._cache = None
            return i
        else:
            return self._it.next()
        #self._cache = None
        #return i

    def _peek_dummy(self):
        if self._cache:
            return self._cache
        else:
            try:
                i = self._it.next()
            except StopIteration:
                return self._dummy
            self._cache = i
            return i

    def _peek_no_dummy(self):
        if self._cache:
            return self._cache
        else:
            i = self._it.next()
            self._cache = i
            return i

    def __iter__(self):
        return self

def print_tokens_simple(lexer):
    while True:
        tok = lexer.token()
        if not tok:
            break
        print tok
