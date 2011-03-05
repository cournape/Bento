import os
import sys

from cPickle \
    import \
        load, dump

from yaku._config \
    import \
        BUILD_DIR, DEFAULT_ENV, BUILD_CONFIG, BUILD_CACHE, CONFIG_CACHE, HOOK_DUMP
from yaku.environment \
    import \
        Environment
from yaku.tools \
    import \
        import_tools
from yaku.utils \
    import \
        ensure_dir, rename
from yaku.errors \
    import \
        UnknownTask
import yaku.node
import yaku.task_manager

def create_top_nodes(start_dir, build_dir):
    root = yaku.node.Node("", None)
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)
    if not os.path.exists(start_dir):
        raise ValueError("%s does not exist ???")
    srcnode = root.find_dir(start_dir)
    bldnode = root.find_dir(build_dir)

    # FIXME
    class _FakeContext(object):
        pass
    yaku.node.Node.ctx = _FakeContext()
    yaku.node.Node.ctx.srcnode = srcnode
    yaku.node.Node.ctx.bldnode = bldnode

    return srcnode, bldnode

# XXX: yet another hack. We need to guarantee that a same file is
# represented by exactly the same node instance (defined as the same
# id) everywhere. Pickling does not guarantee that, so for the files
# mapping, we store the nodes as paths and pickle that. We recreate
# the nodes from there when we need to reload it.
def _hook_id_to_hook_path(hook_dict):
    # convert a hook dict indexed by id to a hook dict indexed by
    # paths (for storage)
    return dict([(k.srcpath(), v) for k, v in hook_dict.items()])

def _hook_path_to_hook_id(src_root, hook_dict):
    # convert a hook dict indexed by paths to a hook dict indexed by
    # id
    return dict([(src_root.find_resource(k), v) for \
                 k, v in hook_dict.items()])

class ConfigureContext(object):
    def __init__(self):
        self.env = Environment()
        self.tools = []
        self._tool_modules = {}
        self.builders = {}
        self.cache = {}
        self.conf_results = []
        self._configured = {}
        self._stdout_cache = {}
        self._cmd_cache = {}

    def load_tool(self, tool, tooldir=None):
        _t = import_tools([tool], tooldir)
        self.tools.append({"tool": tool, "tooldir": tooldir})
        mod = _t[tool]
        self._tool_modules[tool] = mod
        if hasattr(mod, "get_builder"):
            self.builders[tool] = mod.get_builder(self)
        return mod

    def use_tools(self, tools, tooldir=None):
        ret = {}
        for t in tools:
            if t in self._tool_modules:
                _t = self._tool_modules[t]
            else:
                _t = self.load_tool(t, tooldir)
            ret[t] = _t
        self.setup_tools()
        return ret

    def setup_tools(self):
        for builder in self.builders.values():
            if not builder.configured:
               builder.configure()
               self._configured[builder] = True

    def store(self):
        self.env.store(DEFAULT_ENV)

        self.log.close()
        fid = open(CONFIG_CACHE, "wb")
        try:
            dump(self.cache, fid)
            dump(self._stdout_cache, fid)
            dump(self._cmd_cache, fid)
        finally:
            fid.close()

        fid = myopen(BUILD_CONFIG, "w")
        try:
            fid.write("%r\n" % self.tools)
        finally:
            fid.close()

        fid = myopen(HOOK_DUMP, "wb")
        try:
            dump({"extensions": yaku.task_manager.RULES_REGISTRY,
                  "files": _hook_id_to_hook_path(yaku.task_manager.FILES_REGISTRY)},
                 fid)
        finally:
            fid.close()

    def start_message(self, msg):
        sys.stderr.write(msg + "... ")
        self.log.write("=" * 79 + "\n")
        self.log.write("%s\n" % msg)

    def end_message(self, msg):
        sys.stderr.write("%s\n" % msg)

    def set_cmd_cache(self, task, cmd):
        self._cmd_cache[task.get_uid()] = cmd[:]

    def get_cmd(self, task):
        tid = task.get_uid()
        try:
            return self._cmd_cache[tid]
        except KeyError:
            raise UnknownTask

    def set_stdout_cache(self, task, stdout):
        self._stdout_cache[task.get_uid()] = stdout

    def get_stdout(self, task):
        tid = task.get_uid()
        try:
            return self._stdout_cache[tid]
        except KeyError:
            raise UnknownTask

def load_tools(self, fid):
    tools = eval(fid.read())
    for t in tools:
        _t = import_tools([t["tool"]], t["tooldir"])
        tool_name = t["tool"]
        tool_mod = _t[tool_name]
        if hasattr(tool_mod, "get_builder"):
            self.builders[tool_name] = tool_mod.get_builder(self)
        # XXX: this is ugly - need to rethinkg tool
        # initialization/configuration
        if hasattr(tool_mod, "init"):
            tool_mod.init()
    self.tools = tools

class BuildContext(object):
    def __init__(self):
        self.env = Environment()
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

        srcnode, bldnode = create_top_nodes(
                os.path.abspath(os.getcwd()),
                os.path.abspath(self.env["BLDDIR"]))
        self.src_root = srcnode
        self.bld_root = bldnode

        fid = open(HOOK_DUMP, "rb")
        try:
            data = load(fid)
            yaku.task_manager.RULES_REGISTRY = data["extensions"]
            yaku.task_manager.FILES_REGISTRY = _hook_path_to_hook_id(srcnode, data["files"])
        finally:
            fid.close()

    def store(self):
        # Use rename to avoid corrupting the cache if interrupted
        tmp_fid = open(BUILD_CACHE + ".tmp", "wb")
        try:
            dump(self.cache, tmp_fid)
        finally:
            tmp_fid.close()
        rename(BUILD_CACHE + ".tmp", BUILD_CACHE)

    def set_stdout_cache(self, task, stdout):
        pass

    def set_cmd_cache(self, task, stdout):
        pass
def myopen(filename, mode="r"):
    if "w" in mode:
        ensure_dir(filename)
    return open(filename, mode)

def get_cfg():
    ctx = ConfigureContext()
    if os.path.exists(CONFIG_CACHE):
        fid = open(CONFIG_CACHE, "rb")
        try:
            ctx.cache = load(fid)
            ctx._stdout_cache = load(fid)
            ctx._cmd_cache = load(fid)
        finally:
            fid.close()

    # XXX: how to reload existing environment ?
    env = Environment()
    if not env.has_key("BLDDIR"):
        env["BLDDIR"] = BUILD_DIR
    # FIXME: nothing to do here
    env["VERBOSE"] = False
    if "-v" in sys.argv:
        env["VERBOSE"] = True
    # Keep this as is - we do want a dictionary for 'serialization', and python
    # 3 os.environ is an object instead of a dict
    env["ENV"] = dict([(k, v) for k, v in os.environ.items()])

    srcnode, bldnode = create_top_nodes(
            os.path.abspath(os.getcwd()),
            os.path.abspath(env["BLDDIR"]))
    ctx.src_root = srcnode
    ctx.bld_root = bldnode

    ctx.env = env
    ctx.log = myopen(os.path.join(env["BLDDIR"], "config.log"), "w")
    return ctx

def get_bld():
    ctx = BuildContext()
    ctx.load()

    return ctx
