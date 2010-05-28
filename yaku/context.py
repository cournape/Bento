import os
import sys

from cPickle \
    import \
        load, dump

from yaku._config \
    import \
        BUILD_DIR, DEFAULT_ENV, BUILD_CONFIG, BUILD_CACHE, CONFIG_CACHE
from yaku.environment \
    import \
        Environment
from yaku.tools \
    import \
        import_tools
from yaku.utils \
    import \
        ensure_dir

class ConfigureContext(object):
    def __init__(self):
        self.env = {}
        self.tools = []
        self.cache = {}
        self.conf_results = []

        # FIXME: nothing to do here
        self.env["VERBOSE"] = False
        if "-v" in sys.argv:
            self.env["VERBOSE"] = True

    def load_tools(self, tools, tooldir=None):
        for t in tools:
            self.tools.append({"tool": t, "tooldir": tooldir})
            import_tools([t], tooldir)

    def store(self):
        self.env.store(DEFAULT_ENV)

        self.log.close()
        with open(CONFIG_CACHE, "w") as fid:
            dump(self.cache, fid)

        fid = myopen(BUILD_CONFIG, "w")
        try:
            fid.write("%r\n" % self.tools)
        finally:
            fid.close()

class BuildContext(object):
    def __init__(self):
        self.env = {}
        self.tools = []
        self.cache = {}

    def load(self):
        f = open(BUILD_CONFIG)
        try:
            tools = eval(f.read())
            for t in tools:
                import_tools([t["tool"]], t["tooldir"])
        finally:
            f.close()

        if os.path.exists(BUILD_CACHE):
            fid = open(BUILD_CACHE, "rb")
            try:
                self.cache = load(fid)
            finally:
                fid.close()
        else:
            self.cache = {}

        self.env = Environment()
        if os.path.exists(DEFAULT_ENV):
            self.env.load(DEFAULT_ENV)

    def store(self):
        # Use rename to avoid corrupting the cache if interrupted
        tmp_fid = open(BUILD_CACHE + ".tmp", "w")
        try:
            dump(self.cache, tmp_fid)
        finally:
            tmp_fid.close()

        try:
            os.unlink(BUILD_CACHE)
        except OSError:
            pass
        os.rename(BUILD_CACHE + ".tmp", BUILD_CACHE)

def myopen(filename, mode="r"):
    if "w" in mode:
        ensure_dir(filename)
    return open(filename, mode)

def get_cfg():
    ctx = ConfigureContext()
    if os.path.exists(CONFIG_CACHE):
        with open(CONFIG_CACHE) as fid:
            ctx.cache = load(fid)

    if os.path.exists(DEFAULT_ENV):
        env = Environment()
        env.load(DEFAULT_ENV)
    else:
        env = Environment()
    if not env.has_key("BLDDIR"):
        env["BLDDIR"] = BUILD_DIR
    ctx.env = env
    ctx.log = myopen(os.path.join(env["BLDDIR"], "config.log"), "w")
    return ctx

def get_bld():
    ctx = BuildContext()
    ctx.load()
    return ctx
