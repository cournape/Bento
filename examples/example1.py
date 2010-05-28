import os
import sys

from cPickle \
    import \
        load, dump

from yaku.pyext \
    import \
        create_pyext, get_pyenv

from yaku.build_context \
    import \
        get_bld
from yaku.tools \
    import \
        import_tools
from yaku.utils \
    import \
        ensure_dir

from yaku.tools.gcc import detect as gcc_detect

from yaku.conftests \
    import \
        check_compiler, check_header

# Use dot in the name to avoid accidental import of it
CONFIG_INFO = "default.config.py"

def configure(ctx):
    ctx.load_tools(["ctasks"], ["tools"])

    if "-v" in sys.argv:
        ctx.env["VERBOSE"] = True
    gcc_detect(ctx)
    check_compiler(ctx)
    check_header(ctx, "stdio.h")
    ctx.env.update(get_pyenv())

def build(ctx):
    create_pyext(ctx, "_bar", ["src/hellomodule.c"])

BUILD_DIR = "build"
DEFAULT_ENV = os.path.join(BUILD_DIR, "default.env.py")
BUILD_CONFIG = os.path.join(BUILD_DIR, "build.config.py")
CONFIG_CACHE = os.path.join(BUILD_DIR, ".config.pck")
BUILD_CACHE = os.path.join(BUILD_DIR, ".build.pck")

from yaku.environment \
    import \
        Environment

class ConfigureContext(object):
    def __init__(self):
        self.env = {}
        self.tools = []
        self.cache = {}
        self.conf_results = []

    def load_tools(self, tools, tooldir=None):
        for t in tools:
            self.tools.append({"tool": t, "tooldir": tooldir})
            import_tools([t], tooldir)

    def store(self):
        self.env.store(DEFAULT_ENV)

        self.log.close()
        with open(CONFIG_CACHE, "w") as fid:
            dump(self.cache, fid)

class BuildContext(object):
    def __init__(self):
        self.env = {}
        self.tools = {}
        self.cache = {}

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

if __name__ == "__main__":
    ctx = get_cfg()
    configure(ctx)
    ctx.store()
