import os
import sys
import subprocess

if sys.version_info[0] < 3:
    from cPickle \
        import \
            load, dump, dumps
else:
    from pickle \
        import \
            load, dump, dumps

from yaku._config \
    import \
        DEFAULT_ENV, BUILD_CONFIG, BUILD_CACHE, CONFIG_CACHE, HOOK_DUMP, \
        _OUTPUT
from yaku.environment \
    import \
        Environment
from yaku.tools \
    import \
        import_tools
from yaku.utils \
    import \
        ensure_dir, rename, join_bytes
from yaku.errors \
    import \
        UnknownTask, ConfigurationFailure, TaskRunFailure, WindowsError
import yaku.node
import yaku.task_manager

def create_top_nodes(start_dir, build_dir):
    root = yaku.node.Node("", None)
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)
    if not os.path.exists(start_dir):
        raise ValueError("%s does not exist ???" % start_dir)
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

        self.src_root = None
        self.bld_root = None
        self.path = None

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
        default_env = self.bld_root.make_node(DEFAULT_ENV)
        self.env.store(default_env.abspath())

        self.log.close()

        config_cache = self.bld_root.make_node(CONFIG_CACHE)
        out = []
        out.append(dumps(self.cache))
        out.append(dumps(self._stdout_cache))
        out.append(dumps(self._cmd_cache))
        config_cache.write(join_bytes(out), flags="wb")

        build_config = self.bld_root.make_node(BUILD_CONFIG)
        build_config.write("%r\n" % self.tools)

        hook_dump = self.bld_root.make_node(HOOK_DUMP)
        s = dumps({"extensions": yaku.task_manager.RULES_REGISTRY,
                   "files": _hook_id_to_hook_path(yaku.task_manager.FILES_REGISTRY)})
        hook_dump.write(s, flags="wb")

    def start_message(self, msg):
        _OUTPUT.write(msg + "... ")
        self.log.write("=" * 79 + "\n")
        self.log.write("%s\n" % msg)

    def end_message(self, msg):
        _OUTPUT.write("%s\n" % msg)

    def fail_configuration(self, msg):
        msg = "%s\nPlease look at the configuration log %r" % (msg, self.log.name)
        self.log.flush()
        raise ConfigurationFailure(msg)

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

    def try_command(self, cmd, cwd=None, env=None, kw=None):
        if cwd is None:
            cwd = self.bld_root.abspath()
        if kw is None:
            kw = {}
        if env is not None:
            kw["env"] = env

        def log_failure(succeed, explanation):
            if succeed:
                self.log.write("---> Succeeded !\n")
            else:
                self.log.write("---> Failure !\n")
                self.log.write("~~~~~~~~~~~~~~\n")
                self.log.write(explanation)
                self.log.write("~~~~~~~~~~~~~~\n")
            self.log.write("Command was:\n")
            self.log.write("%s\n" % cmd)
            self.log.write("\n")

        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, cwd=cwd, **kw)
            stdout = p.communicate()[0].decode("utf-8")
            log_failure(p.returncode == 0, stdout)
            if p.returncode:
                return False
            return True
        except OSError:
            e = get_exception()
            log_failure(False, str(e))
        except WindowsError:
            e = get_exception()
            log_failure(False, str(e))
        return False

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

    def load(self, src_path=None, build_path="build"):
        if src_path is None:
            src_path = os.getcwd()
        src_path = os.path.abspath(src_path)
        build_path = os.path.abspath(os.path.join(os.getcwd(), build_path))
        if not os.path.exists(build_path):
            raise IOError("%s not found (did you use different build_path for configure and build contexts ?)" \
                          % build_path)

        srcnode, bldnode = create_top_nodes(src_path, build_path)
        self.src_root = srcnode
        self.bld_root = bldnode
        self.path = srcnode

        self.env = Environment()
        default_env = bldnode.find_node(DEFAULT_ENV)
        if default_env:
            self.env.load(default_env.abspath())
        if not os.path.abspath(self.env["BLDDIR"]) == bldnode.abspath():
            raise ValueError("Gne ?")

        build_config = bldnode.find_node(BUILD_CONFIG)
        if build_config is None:
            raise IOError("Did not find %r in %r" % (BUILD_CONFIG, bldnode.abspath()))
        else:
            f = open(build_config.abspath())
            try:
                load_tools(self, f)
            finally:
                f.close()

        build_cache = bldnode.find_node(BUILD_CACHE)
        if build_cache is not None:
            fid = open(build_cache.abspath(), "rb")
            try:
                self.cache = load(fid)
            finally:
                fid.close()
        else:
            self.cache = {}

        hook_dump = bldnode.find_node(HOOK_DUMP)
        fid = open(hook_dump.abspath(), "rb")
        try:
            data = load(fid)
            yaku.task_manager.RULES_REGISTRY = data["extensions"]
            yaku.task_manager.FILES_REGISTRY = _hook_path_to_hook_id(srcnode, data["files"])
        finally:
            fid.close()

    def store(self):
        build_cache = self.bld_root.make_node(BUILD_CACHE)
        tmp_fid = open(build_cache.abspath() + ".tmp", "wb")
        try:
            dump(self.cache, tmp_fid)
        finally:
            tmp_fid.close()
        rename(build_cache.abspath() + ".tmp", build_cache.abspath())

    def set_stdout_cache(self, task, stdout):
        pass

    def set_cmd_cache(self, task, stdout):
        pass

def myopen(filename, mode="r"):
    if "w" in mode:
        ensure_dir(filename)
    return open(filename, mode)

def get_cfg(src_path=None, build_path="build"):
    ctx = ConfigureContext()
    config_cache = os.path.join(build_path, CONFIG_CACHE)
    if os.path.exists(config_cache):
        fid = open(config_cache, "rb")
        try:
            ctx.cache = load(fid)
            ctx._stdout_cache = load(fid)
            ctx._cmd_cache = load(fid)
        finally:
            fid.close()

    # XXX: how to reload existing environment ?
    env = Environment()
    if not "BLDDIR" in env:
        env["BLDDIR"] = build_path
    # FIXME: nothing to do here
    env["VERBOSE"] = False
    if "-v" in sys.argv:
        env["VERBOSE"] = True
    # Keep this as is - we do want a dictionary for 'serialization', and python
    # 3 os.environ is an object instead of a dict
    env["ENV"] = dict([(k, v) for k, v in os.environ.items()])

    if src_path is None:
        src_path = os.getcwd()
    srcnode, bldnode = create_top_nodes(
            os.path.abspath(src_path),
            os.path.abspath(env["BLDDIR"]))
    ctx.src_root = srcnode
    ctx.bld_root = bldnode
    # src_root and bld_root never change, but path may. All source nodes are
    # created relatively to path (kinda 'virtual' cwd)
    ctx.path = srcnode

    ctx.env = env
    ctx.log = myopen(os.path.join(env["BLDDIR"], "config.log"), "w")
    return ctx

def get_bld(src_path=None, build_path="build"):
    ctx = BuildContext()
    ctx.load(src_path=src_path, build_path=build_path)

    return ctx
