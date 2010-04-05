import functools

from cPickle \
    import \
        loads, dumps

def pickle_memoize(fctn):
    """Pickle-based function memoizer.

    Each new returned value is pickled, and unpickled when taken from the
    cache.  It is relatively slow, and only makes sense for functions which
    return big objects and which take a long time to create."""
    memory = {}
    @functools.wraps(fctn)
    def memo(*args,**kwargs):
        haxh = dumps((args, sorted(kwargs.iteritems())), protocol=-1)
        if haxh not in memory:
            res = fctn(*args, **kwargs)
            memory[haxh] = dumps(res, protocol=-1)
            return res
        return loads(memory[haxh])

    if memo.__doc__:
        memo.__doc__ = "\n".join([memo.__doc__,"This function is memoized."])
    return memo

