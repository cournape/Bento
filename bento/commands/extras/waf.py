import os
import sys
import shutil
import logging
import collections

import os.path as op

import bento

from bento.commands.api \
    import \
        UsageException

import six

if "WAFDIR" in os.environ:
    WAFDIR = os.path.join(os.environ["WAFDIR"], "waflib")
else:
    WAFDIR = op.abspath(op.join(op.dirname(bento.__file__), os.pardir, "waflib"))
    if not op.exists(WAFDIR):
        WAFDIR = os.path.join(os.getcwd(), "waflib")
if not os.path.exists(WAFDIR):
    raise UsageException("""\
%r not found: required when using waf extras !
    You can set waf location using the WAFDIR environment variable, such as
    $WAFDIR contains the 'waflib' directory""" % WAFDIR)
sys.path.insert(0, os.path.dirname(WAFDIR))

from waflib.Context \
    import \
        create_context
from waflib.Options \
    import \
        OptionsContext
from waflib import Options
from waflib import Context
from waflib import Logs
from waflib import Build
from waflib import Utils
import waflib

from bento.core.node_package \
    import \
        translate_name
from bento.commands.options \
    import \
        Option
from bento.commands.context \
    import \
        ConfigureContext, BuildContext
from bento.installed_package_description \
    import \
        InstalledSection
from bento.core.utils \
    import \
        normalize_path

WAF_TOP = os.path.join(WAFDIR, os.pardir)

WAF_CONFIG_LOG = 'config.log'

__USE_NO_OUTPUT_LOGGING = False
def disable_output():
    # Make Betty proud...
    global __USE_NO_OUTPUT_LOGGING
    __USE_NO_OUTPUT_LOGGING = True

def make_stream_logger(name, stream):
    # stream should be a file-like object supporting write/read/?
    logger = logging.getLogger(name)
    hdlr = logging.StreamHandler(stream)
    formatter = logging.Formatter('%(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.DEBUG)
    return logger

def _init_log_no_output():
    # XXX: all this heavily plays with waf internals - only use for unit
    # testing bento where waf output screws up nose own output/logging magic
    from six.moves import cStringIO
    Logs.got_tty = False
    Logs.get_term_cols = lambda: 80
    Logs.get_color = lambda cl: ''
    Logs.colors = Logs.color_dict()

    fake_output = cStringIO()
    def fake_pprint(col, str, label='', sep='\n'):
        fake_output.write("%s%s%s %s%s" % (Logs.colors(col), str, Logs.colors.NORMAL, label, sep))

    Logs.pprint = fake_pprint

    log = logging.getLogger('waflib')
    log.handlers = []
    log.filters = []
    hdlr = logging.StreamHandler(cStringIO())
    hdlr.setFormatter(Logs.formatter())
    log.addHandler(hdlr)
    log.addFilter(Logs.log_filter())
    log.setLevel(logging.DEBUG)
    Logs.log = log

def _init(run_path, source_path, build_path):
    if not (os.path.isabs(run_path) and os.path.isabs(source_path) and os.path.isabs(build_path)):
        raise ValueError("All paths must be absolute !")
    tooldir = os.path.join(WAFDIR, "Tools")

    sys.path.insert(0, tooldir)
    cwd = os.getcwd()

    if __USE_NO_OUTPUT_LOGGING is True:
        _init_log_no_output()
    else:
        Logs.init_log()

    class FakeModule(object):
        pass
    Context.g_module = FakeModule
    Context.g_module.root_path = os.path.abspath(__file__)
    Context.g_module.top = source_path
    Context.g_module.out = build_path

    Context.top_dir = source_path
    Context.run_dir = run_path
    Context.out_dir = build_path
    Context.waf_dir = WAF_TOP
    Context.launch_dir = run_path

def register_options(global_context):
    opt = Option("-p", "--progress", help="Use progress bar", action="store_true", dest="progress_bar")
    global_context.add_option("build", opt)

class ConfigureWafContext(ConfigureContext):
    def __init__(self, global_context, cmd_argv, options_context, pkg, run_node):
        super(ConfigureWafContext, self).__init__(global_context, cmd_argv, options_context, pkg, run_node)

        run_path = self.run_node.abspath()
        source_path = self.top_node.abspath()
        build_path = self.build_node.abspath()
        _init(run_path=run_path, source_path=source_path, build_path=build_path)

        opts = OptionsContext()
        opts.load("compiler_c")
        opts.parse_args([])
        self.waf_options_context = opts

        waf_context = create_context("configure", run_dir=source_path)
        waf_context.options = Options.options
        waf_context.init_dirs()
        waf_context.cachedir = waf_context.bldnode.make_node(Build.CACHE_DIR)
        waf_context.cachedir.mkdir()

        path = os.path.join(waf_context.bldnode.abspath(), WAF_CONFIG_LOG)
        waf_context.logger = Logs.make_logger(path, 'cfg')
        self.waf_context = waf_context

        # FIXME: this is wrong (not taking into account sub packages)
        has_compiled_code = len(pkg.extensions) > 0 or len(pkg.compiled_libraries) > 0
        if not has_compiled_code:
            if pkg.subpackages:
                for v in pkg.subpackages.values():
                    if len(v.extensions) > 0 or len(v.compiled_libraries) > 0:
                        has_compiled_code = True
                        break
        conf = self.waf_context
        if has_compiled_code:
            conf.load("compiler_c")
            conf.env["PYTHON"] = [sys.executable]
            conf.load("python")
            conf.check_python_version((2,4,2))
            conf.check_python_headers()
        self._old_path = None

    def pre_recurse(self, local_node):
        ConfigureContext.pre_recurse(self, local_node)
        self._old_path = self.waf_context.path
        # Gymnastic to make a *waf* node from a *bento* node
        self.waf_context.path = self.waf_context.path.make_node(self.local_node.srcpath())

    def post_recurse(self):
        self.waf_context.path = self._old_path
        ConfigureContext.post_recurse(self)

    def shutdown(self):
        super(ConfigureWafContext, self).shutdown()
        self.waf_context.store()

def ext_name_to_path(name):
    """Convert extension name to path - the path does not include the
    file extension

    Example: foo.bar -> foo/bar
    """
    return name.replace('.', os.path.sep)

class BentoBuildContext(Build.BuildContext):
    """Waf build context with additional support to register builder output to
    bento build context."""
    def __init__(self, *a, **kw):
        Build.BuildContext.__init__(self, *a, **kw)
        # XXX: set into BuildWafContext
        self.bento_context = None

    def register_outputs(self, category, name, outputs):
        outputs_registry = self.bento_context.outputs_registry

        # waf -> bento nodes translations
        nodes = [self.bento_context.build_node.make_node(n.bldpath()) for n in outputs]
        from_node = self.bento_context.build_node.find_node(outputs[0].parent.bldpath())

        pkg_dir = os.path.dirname(name.replace('.', os.path.sep))
        target_dir = os.path.join('$sitedir', pkg_dir)
        outputs_registry.register_outputs(category, name, nodes, from_node, target_dir)

@waflib.TaskGen.feature("bento")
@waflib.TaskGen.before_method("apply_link")
def apply_pyext_target_renaming(self):
    if not self.target:
        self.target = self.name
    self.target = self.target.replace(".", os.sep)

@waflib.TaskGen.feature("bento")
@waflib.TaskGen.after_method("apply_link")
def apply_register_outputs(self):
    for x in self.features:
        if x == "cprogram" and "cxx" in self.features:
            x = "cxxprogram"
        if x == "cshlib" and "cxx" in self.features:
            x = "cxxshlib"

        if x in waflib.Task.classes:
            if issubclass(waflib.Task.classes[x], waflib.Tools.ccroot.link_task):
                link = x
                break
    else:
        return

    if "pyext" in self.features and "cshlib" in self.features:
        category = "extensions"
    else:
        category = "compiled_libraries"
    bento_context = self.bld.bento_context
    ref_node = bento_context.top_node.make_node(self.path.path_from(self.path.ctx.srcnode))
    name = translate_name(self.name, ref_node, bento_context.top_node)
    self.bld.register_outputs(category, name, self.link_task.outputs)

class BuildWafContext(BuildContext):
    def pre_recurse(self, local_node):
        super(BuildWafContext, self).pre_recurse(local_node)
        self._old_path = self.waf_context.path
        # Gymnastic to make a *waf* node from a *bento* node
        self.waf_context.path = self.waf_context.path.make_node(self.local_node.srcpath())

    def post_recurse(self):
        self.waf_context.path = self._old_path
        super(BuildWafContext, self).post_recurse()

    def __init__(self, global_context, cmd_argv, options_context, pkg, run_node):
        super(BuildWafContext, self).__init__(None, cmd_argv, options_context, pkg, run_node)

        o, a = options_context.parser.parse_args(cmd_argv)
        if o.jobs:
            jobs = int(o.jobs)
        else:
            jobs = 1
        if o.verbose:
            verbose = int(o.verbose)
            zones = ["runner"]
        else:
            verbose = 0
            zones = []
        if o.inplace:
            self.inplace = 1
        else:
            self.inplace = 0
        if o.progress_bar:
            self.progress_bar = True
        else:
            self.progress_bar = False

        Logs.verbose = verbose
        Logs.init_log()
        if zones is None:
            Logs.zones = []
        else:
            Logs.zones = zones

        run_path = self.run_node.abspath()
        source_path = self.top_node.abspath()
        build_path = self.build_node.abspath()
        _init(run_path=run_path, source_path=source_path, build_path=build_path)
        waf_context = create_context("build")
        waf_context.restore()
        if not waf_context.all_envs:
            waf_context.load_envs()
        waf_context.jobs = jobs
        waf_context.timer = Utils.Timer()
        if self.progress_bar:
            waf_context.progress_bar = 1
        waf_context.bento_context = self
        self.waf_context = waf_context

        def _default_extension_builder(extension, **kw):
            if not "features" in kw:
                kw["features"] = "c cshlib pyext bento"
            if not "source" in kw:
                kw["source"] = extension.sources[:]
            if not "name" in kw:
                kw["name"] = extension.name
            return self.waf_context(**kw)

        def _default_library_builder(library, **kw):
            if not "features" in kw:
                kw["features"] = "c cstlib pyext bento"
            if not "source" in kw:
                kw["source"] = library.sources[:]
            if not "name" in kw:
                kw["name"] = library.name
            return self.waf_context(**kw)

        self.builder_registry.register_category("extensions", _default_extension_builder)
        self.builder_registry.register_category("compiled_libraries", _default_library_builder)

    def compile(self):
        super(BuildWafContext, self).compile()
        reg = self.builder_registry

        for category in ("extensions", "compiled_libraries"):
            for name, extension in self._node_pkg.iter_category(category):
                builder = reg.builder(category, name)
                self.pre_recurse(extension.ref_node)
                try:
                    extension = extension.extension_from(extension.ref_node)
                    task_gen = builder(extension)
                finally:
                    self.post_recurse()

        if self.progress_bar:
            sys.stderr.write(Logs.colors.cursor_off)
        try:
            self.waf_context.compile()
        finally:
            if self.progress_bar:
                c = len(self.waf_context.returned_tasks) or 1
                self.waf_context.to_log(self.waf_context.progress_line(c, c, Logs.colors.BLUE, Logs.colors.NORMAL))
                print('')
                sys.stdout.flush()
                sys.stderr.write(Logs.colors.cursor_on)

    def shutdown(self):
        super(BuildWafContext, self).shutdown()
        self.waf_context.store()
