from toydist.utils \
    import \
        pickle_memoize
from toydist.core.parser.parser \
    import \
        parse as _parse
from toydist.core.parser.nodes \
    import \
        ast_walk
from toydist.core.parser.visitor \
    import \
        Dispatcher

@pickle_memoize
def parse(data):
    return _parse(data)

def parse_to_dict(data, user_flags=None):
    p = parse(data)

    dispatcher = Dispatcher()
    if user_flags is None:
        dispatcher._vars = {}
    else:
        dispatcher._vars = user_flags

    res = ast_walk(p, dispatcher)
    return res
