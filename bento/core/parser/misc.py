import os

try:
    from hashlib import md5
except ImportError:
    from md5 import md5

try:
    from cPickle import dump, load
except ImportError:
    from pickle import dump, load

from bento.compat.api \
    import \
        rename
from bento._config \
    import \
        BENTO_SCRIPT, PKG_CACHE
from bento.core.utils \
    import \
        ensure_dir
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

# XXX: Make a decorator to make this reusable in other parts of
# bento
def get_parsed_script(data):
    """Return parsed dictionary of the given file content, but cache
    the result so that one does not have to parse the same content
    twice.
    
    Note
    ----
    It should be safe to use this instead of parse. The cache is
    invalidated when the content of data is different (checksum).

    """
    checksum = md5(data).hexdigest()

    def parse_and_store_pkg():
        # Write to a temp file to avoid writing corrupted file if
        # ctrl+c is caught during write
        p = _parse(data)

        # We keep a dict of cached parsed strings indexed by checksums
        # FIXME: we should use a LRU cache, because as is, the cache keeps growing
        if os.path.exists(PKG_CACHE):
            f = open(PKG_CACHE, "rb")
            try:
                d = load(f)
            finally:
                f.close()
        else:
            d = {}
        d[checksum] = p

        pkg_cache_tmp = PKG_CACHE + ".tmp"
        ensure_dir(pkg_cache_tmp)
        tmp = open(pkg_cache_tmp, "wb")
        try:
            dump(d, tmp)
        finally:
            tmp.close()

        rename(pkg_cache_tmp, PKG_CACHE)
        return p

    if not os.path.exists(PKG_CACHE):
        p = parse_and_store_pkg()
    else:
        fid = open(PKG_CACHE, "rb")
        try:
            d = load(fid)
            if not d.has_key(checksum):
                p = parse_and_store_pkg()
            else:
                p = d[checksum]
        finally:
            fid.close()

    return p

def parse_to_dict(data, user_flags=None, filename=None):
    """Parse the given data to a dictionary which is easy to exploit
    at later stages."""
    try:
        p = get_parsed_script(data)
    except ParseError, e:
        # XXX: hack to add filename information
        e.filename = filename
        raise

    dispatcher = Dispatcher(user_flags)
    res = ast_walk(p, dispatcher)
    return res
