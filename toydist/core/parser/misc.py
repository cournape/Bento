import os

try:
    from hashlib import md5
except ImportError:
    from md5 import md5

try:
    from cPickle import dump, load
except ImportError:
    from pickle import dump, load

from toydist._config \
    import \
        TOYDIST_SCRIPT, PKG_CACHE
from toydist.core.utils \
    import \
        ensure_directory
from toydist.core.parser.parser \
    import \
        parse as _parse
from toydist.core.parser.nodes \
    import \
        ast_walk
from toydist.core.parser.visitor \
    import \
        Dispatcher

# XXX: Make a decorator to make this reusable in other parts of
# toydist
def get_parsed_script(data):
    """Return parsed dictionary of the given file content, but cache
    the result so that one does not have to parse the same content
    twice.
    
    Note
    ----
    It should be safe to use this instead of parse. The cache is
    invalidated when the content of data is different (checksum)
    """
    checksum = md5(data).hexdigest()

    def parse_and_store_pkg():
        # Write to a temp file to avoid writing corrupted file if
        # ctrl+c is caught during write
        p = _parse(data)
        ensure_directory(PKG_CACHE + ".tmp")
        tmp = open(PKG_CACHE + ".tmp", "wb")
        try:
            dump(p, tmp)
            dump(checksum, tmp)
        finally:
            tmp.close()

        os.rename(PKG_CACHE + ".tmp", PKG_CACHE)
        return p

    if not os.path.exists(PKG_CACHE):
        p = parse_and_store_pkg()
    else:
        fid = open(PKG_CACHE, "rb")
        try:
            p = load(fid)
            stored_checksum = load(fid)
            if not stored_checksum == checksum:
                p = parse_and_store_pkg()
        finally:
            fid.close()

    return p

def parse_to_dict(data, user_flags=None):
    p = get_parsed_script(data)

    dispatcher = Dispatcher()
    if user_flags is None:
        dispatcher._vars = {}
    else:
        dispatcher._vars = user_flags

    res = ast_walk(p, dispatcher)
    return res
