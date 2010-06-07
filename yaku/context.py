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
        self._tool_modules = {}
        self.builders = {}
        self.cache = {}
        self.conf_results = []

    def load_tool(self, tool, tooldir=None):
        _t = import_tools([tool], tooldir)
        self.tools.append({"tool": tool, "tooldir": tooldir})
        mod = _t[tool]
        self._tool_modules[tool] = mod
        if hasattr(mod, "get_builder"):
            self.builders[tool] = mod.get_builder(self)
        if not hasattr(mod, "configure"):
            mod.configure = lambda x: None
        return mod

    def use_tools(self, tools, tooldir=None):
        ret = {}
        for t in tools:
            _t = self.load_tool(t, tooldir)
            ret[t] = _t
        for mod in self._tool_modules.values():
            mod.configure(self)
        return ret

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

def load_tools(self, fid):
    tools = eval(fid.read())
    for t in tools:
        _t = import_tools([t["tool"]], t["tooldir"])
        tool_name = t["tool"]
        tool_mod = _t[tool_name]
        if hasattr(tool_mod, "get_builder"):
            self.builders[tool_name] = tool_mod.get_builder(self)
    self.tools = tools

class BuildContext(object):
    def __init__(self):
        self.env = {}
        self.tools = []
        self.cache = {}
        self.builders = {}
        self.tasks = []

    def load(self):
        self.env = Environment()
        if os.path.exists(DEFAULT_ENV):
            self.env.load(DEFAULT_ENV)

        f = open(BUILD_CONFIG)
        try:
            load_tools(self, f)
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

    if os.path.exists(BUILD_CONFIG):
        fid = myopen(BUILD_CONFIG, "rb")
        try:
            load_tools(ctx, fid)
        finally:
            fid.close()

    if os.path.exists(DEFAULT_ENV):
        env = Environment()
        env.load(DEFAULT_ENV)
    else:
        env = Environment()
    if not env.has_key("BLDDIR"):
        env["BLDDIR"] = BUILD_DIR
    # FIXME: nothing to do here
    env["VERBOSE"] = False
    if "-v" in sys.argv:
        env["VERBOSE"] = True

    ctx.env = env
    ctx.log = myopen(os.path.join(env["BLDDIR"], "config.log"), "w")
    return ctx

def get_bld():
    ctx = BuildContext()
    ctx.load()
    return ctx
