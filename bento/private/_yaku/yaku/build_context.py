import os

from cPickle \
    import \
        load, dump

from yaku.utils \
    import \
        rename

CACHE_FILE = ".cache.lock"

class BuildContext(object):
    def __init__(self):
        self.object_tasks = []
        self.cache = {}
        self.env = {}

    def load(self):
        if os.path.exists(CACHE_FILE):
            fid = open(CACHE_FILE, "rb")
            try:
                self.cache = load(fid)
            finally:
                fid.close()
        else:
            self.cache = {}

    def save(self):
        # Use rename to avoid corrupting the cache if interrupted
        tmp_fid = open(CACHE_FILE + ".tmp", "w")
        try:
            dump(self.cache, tmp_fid)
        finally:
            tmp_fid.close()
        rename(CACHE_FILE + ".tmp", CACHE_FILE)

def get_bld():
    bld = BuildContext()
    bld.load()

    bld.env.update({
            "VERBOSE": False,
            "BLDDIR": "build"})

    return bld

