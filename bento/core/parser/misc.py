from bento.core.parser.parser \
    import \
        parse as _parse
from bento.core.parser.nodes \
    import \
        ast_walk
from bento.core.parser.visitor \
    import \
        Dispatcher
from bento.core.parser.errors \
    import \
        ParseError

def parse_to_dict(data, user_flags=None, filename=None):
    """Parse the given data to a dictionary which is easy to exploit
    at later stages."""
    try:
        p = _parse(data)
        print "HJK"
    except ParseError, e:
        # XXX: hack to add filename information
        e.filename = filename
        raise

    dispatcher = Dispatcher(user_flags)
    res = ast_walk(p, dispatcher)
    return res
