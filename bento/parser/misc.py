from bento.utils.utils \
    import \
        extract_exception
from bento.errors \
    import \
        ParseError
from bento.parser.nodes \
    import \
        ast_walk
from bento.parser.parser \
    import \
        parse as _parse
from bento.parser.visitor \
    import \
        Dispatcher

def raw_parse(data, filename=None):
    try:
        ret = _parse(data)
        return ret
    except ParseError:
        e = extract_exception()
        e.filename = filename
        raise

def build_ast_from_raw_dict(raw_dict, user_flags=None):
    dispatcher = Dispatcher(user_flags)
    res = ast_walk(raw_dict, dispatcher)
    return res

def build_ast_from_data(data, user_flags=None, filename=None):
    """Parse the given data to a dictionary which is easy to exploit
    at later stages."""
    d = raw_parse(data, filename)
    return build_ast_from_raw_dict(d, user_flags)
