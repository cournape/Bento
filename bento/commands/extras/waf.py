import os
import sys
import shutil
import logging
import collections

if os.environ.has_key("WAFDIR"):
    WAFDIR = os.path.join(os.environ["WAFDIR"], "waflib")
else:
    WAFDIR = os.path.join(os.getcwd(), "waflib")
if not os.path.exists(WAFDIR):
    raise RuntimeError("%r not found: required when using waf extras !" % WAFDIR)
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
    from cStringIO import StringIO
    Logs.got_tty = False
    Logs.get_term_cols = lambda: 80
    Logs.get_color = lambda cl: ''
    Logs.colors = Logs.color_dict()

    fake_output = StringIO()
    def fake_pprint(col, str, label='', sep='\n'):
        fake_output.write("%s%s%s %s%s" % (Logs.colors(col), str, Logs.colors.NORMAL, label, sep))

    Logs.pprint = fake_pprint

    log = logging.getLogger('waflib')
    log.handlers = []
    log.filters = []
    hdlr = logging.StreamHandler(StringIO())
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

    opts = OptionsContext()
    opts.parse_args([])
    opts.load("compiler_c")
    Options.options.check_c_compiler = "gcc"

class ConfigureWafContext(ConfigureContext):
    def __init__(self, cmd_argv, options_context, pkg, run_node):
        super(ConfigureWafContext, self).__init__(cmd_argv, options_context, pkg, run_node)

        run_path = self.run_node.abspath()
        source_path = self.top_node.abspath()
        build_path = self.build_node.abspath()
        _init(run_path=run_path, source_path=source_path, build_path=build_path)
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
        conf = self.waf_context
        try:
            if has_compiled_code:
                conf.load("compiler_c")
                conf.load("python")
                conf.check_python_version((2,4,2))
                conf.check_python_headers()

                # HACK for mac os x
                if sys.platform == "darwin":
                    conf.env["CC"] = ["/usr/bin/gcc-4.0"]
        finally:
            conf.store()

        self._old_path = None

    def pre_recurse(self, local_node):
        ConfigureContext.pre_recurse(self, local_node)
        self._old_path = self.waf_context.path
        # Gymnastic to make a *waf* node from a *bento* node
        self.waf_context.path = self.waf_context.path.make_node(self.local_node.srcpath())

    def post_recurse(self):
        self.waf_context.path = self._old_path
        ConfigureContext.post_recurse(self)

def ext_name_to_path(name):
    """Convert extension name to path - the path does not include the
    file extension

    Example: foo.bar -> foo/bar
    """
    return name.replace('.', os.path.sep)

class BuildWafContext(BuildContext):
    def pre_recurse(self, local_node):
        super(BuildWafContext, self).pre_recurse(local_node)
        self._old_path = self.waf_context.path
        # Gymnastic to make a *waf* node from a *bento* node
        self.waf_context.path = self.waf_context.path.make_node(self.local_node.srcpath())

    def post_recurse(self):
        self.waf_context.path = self._old_path
        super(BuildWafContext, self).post_recurse()

    def __init__(self, cmd_argv, options_context, pkg, run_node):
        super(BuildWafContext, self).__init__(cmd_argv, options_context, pkg, run_node)

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
        self.waf_context = waf_context

        def _default_extension_builder(extension):
            # FIXME: should be handled in the waf builder itself maybe ?
            target = extension.name.replace(".", os.sep)
            return self.waf_context(features='c cshlib pyext',
                                    source=extension.sources, target=target,
                                    name=extension.name)

        def _default_library_builder(library):
            return self.waf_context(features='c cstlib pyext', source=library.sources, target=library.name)

        self.builder_registry.register_category("extensions", _default_extension_builder)
        self.builder_registry.register_category("compiled_libraries", _default_library_builder)


    def compile(self):
        reg = self.builder_registry

        for category in ("extensions", "compiled_libraries"):
            self._outputs[category] = {}
            for name, extension in self._node_pkg.iter_category(category):
                builder = reg.builder(category, name)
                self.pre_recurse(extension.ref_node)
                try:
                    extension = extension.extension_from(extension.ref_node)
                    task_gen = builder(extension)
                finally:
                    self.post_recurse()
                self._outputs[category][name] = []

        from bento.core.recurse import translate_name

        bld = self.waf_context
        bld.compile()

        for group in bld.groups:
            for task_gen in group:
                if hasattr(task_gen, "link_task"):
                    if "cstlib" in task_gen.features:
                        category = "compiled_libraries"
                    else:
                        category = "extensions"
                    ref_node = self.top_node.make_node(task_gen.path.path_from(task_gen.path.ctx.srcnode))
                    name = translate_name(task_gen.name, ref_node, self.top_node)
                    self._outputs[category][name] = [o.bldpath() for o in task_gen.link_task.outputs]
                    if self.inplace:
                        for output in task_gen.link_task.outputs:
                            if output.is_child_of(bld.bldnode):
                                shutil.copy(output.abspath(), output.path_from(bld.bldnode))
