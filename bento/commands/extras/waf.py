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

def _init():
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
    Context.g_module.top = os.getcwd()
    Context.g_module.out = os.path.join(os.getcwd(), "build")

    Context.top_dir = os.getcwd()
    Context.run_dir = os.getcwd()
    Context.out_dir = os.path.join(os.getcwd(), "build")
    Context.waf_dir = WAF_TOP

    opts = OptionsContext()
    opts.parse_args([])
    opts.load("compiler_c")
    Options.options.check_c_compiler = "gcc"

class ConfigureWafContext(ConfigureContext):
    def __init__(self, cmd_argv, options_context, pkg, top_node):
        super(ConfigureWafContext, self).__init__(cmd_argv, options_context, pkg, top_node)

        _init()
        waf_context = create_context("configure")
        waf_context.options = Options.options
        #waf_context.execute()
        waf_context.init_dirs()
        waf_context.cachedir = waf_context.bldnode.make_node(Build.CACHE_DIR)
        waf_context.cachedir.mkdir()

        path = os.path.join(waf_context.bldnode.abspath(), WAF_CONFIG_LOG)
        waf_context.logger = Logs.make_logger(path, 'cfg')
        self.waf_context = waf_context

        if pkg.extensions:
            conf = self.waf_context
            
            conf.load("compiler_c")
            conf.load("python")
            conf.check_python_version((2,4,2))
            conf.check_python_headers()

            # HACK for mac os x
            if sys.platform == "darwin":
                conf.env["CC"] = ["/usr/bin/gcc-4.0"]
            conf.store()

        self._old_path = None

    def pre_recurse(self, local_node):
        ConfigureContext.pre_recurse(self, local_node)
        self._old_path = self.waf_context.path
        # Gymnastic to make a *waf* node from a *bento* node
        self.waf_context.path = self.waf_context.path.make_node(self.local_node.path_from(self.top_node))

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
    def __init__(self, cmd_argv, options_context, pkg, top_node):
        super(BuildWafContext, self).__init__(cmd_argv, options_context, pkg, top_node)

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

        Logs.verbose = verbose
        Logs.init_log()
        if zones is None:
            Logs.zones = []
        else:
            Logs.zones = zones

        _init()
        waf_context = create_context("build")
        waf_context.restore()
        if not waf_context.all_envs:
            waf_context.load_envs()
        waf_context.jobs = jobs
        self.waf_context = waf_context

    def post_compile(self, section_writer):
        bld = self.waf_context
        bld.compile()
        for group in bld.groups:
            for task_gen in group:
                if hasattr(task_gen, "link_task"):
                    if task_gen.path != bld.srcnode:
                        pkg_dir = task_gen.path.srcpath()
                    else:
                        pkg_dir = ""
                    if "cstlib" in task_gen.features:
                        category = "compiled_libraries"
                    else:
                        category = "extensions"
                    name = task_gen.name
                    source_dir = task_gen.link_task.outputs[0].parent.path_from(bld.srcnode)
                    target = os.path.join("$sitedir", pkg_dir)
                    files = [o.name for o in task_gen.link_task.outputs]

                    section = InstalledSection.from_source_target_directories(category, name,
                                            source_dir, target, files)
                    section_writer.sections[category][name] = section

        if self.inplace:
           for g in bld.groups:
                for task_gen in g:
                    if hasattr(task_gen, "link_task"):
                        ltask = task_gen.link_task
                        for output in ltask.outputs:
                            if output.is_child_of(bld.bldnode):
                                shutil.copy(output.abspath(), output.path_from(bld.bldnode))

    def build_extensions_factory(self, *a, **kw):
        def _full_name(extension, local_node):
            if local_node != self.top_node:
                parent = local_node.path_from(self.top_node).split(os.path.sep)
                return ".".join(parent + [extension.name])
            else:
                return extension.name

        def build_grandmaster(pkg):
            def _default_builder(bld, extension):
                bld(features='c cshlib pyext', source=extension.sources,
                    target=extension.name)

            bld = self.waf_context

            # Gather all extensions together with their local_node
            extensions = []
            for extension in pkg.extensions.values():
                local_node = self.top_node.find_dir(".")
                extensions.append((extension, local_node))
            for spkg in pkg.subpackages.values():
                for extension in spkg.extensions.values():
                    local_node = self.top_node.find_dir(spkg.rdir)
                    extensions.append((extension, local_node))

            for extension, local_node in extensions:
                full_name = _full_name(extension, local_node)
                builder = self._extensions_callback.get(full_name, _default_builder)

                old_path = bld.path
                bld.path = old_path.find_dir(local_node.path_from(self.top_node))
                try:
                    builder(bld, extension)
                finally:
                    bld.path = old_path

            return {}
        return build_grandmaster

    def build_compiled_libraries_factory(self, *a, **kw):
        def builder(pkg):
            def _default_builder(bld, library):
                bld(features='c cstlib pyext', source=library.sources, target=library.name)
            bld = self.waf_context
            libraries = []
            for library in pkg.compiled_libraries.values():
                local_node = self.top_node.find_dir(".")
                libraries.append((library, local_node))
            for spkg in pkg.subpackages.values():
                for library in spkg.compiled_libraries.values():
                    local_node = self.top_node.find_dir(spkg.rdir)
                    libraries.append((library, local_node))

            for library, local_node in libraries:
                if local_node != self.top_node:
                    parent = local_node.path_from(self.top_node)
                else:
                    parent = ""
                full_name = os.path.join(parent, library.name)
                builder = self._clibraries_callback.get(full_name, _default_builder)

                old_path = bld.path
                bld.path = old_path.find_dir(local_node.path_from(self.top_node))
                try:
                    builder(bld, library)
                finally:
                    bld.path = old_path

            return {}
        return builder

# We need to fix build / section writing interaction so that InstalledSection
# instances can be written after SectionWriter callback has been called. This
# way that build_installed_section is called only once, and we don't need those
# hacks to enable multiple build_install_sections calls over the same task
# groups
def build_installed_sections(bld, category, task_gen_filter):
    sections = {}
    for group in bld.groups:
        for task_gen in group:
            if hasattr(task_gen, "link_task") and task_gen_filter(task_gen):
                if task_gen.path != bld.srcnode:
                    pkg_dir = task_gen.path.srcpath()
                else:
                    pkg_dir = ""
                name = task_gen.name
                source_dir = task_gen.link_task.outputs[0].parent.path_from(bld.srcnode)
                target = os.path.join("$sitedir", pkg_dir)
                files = [o.name for o in task_gen.link_task.outputs]

                section = InstalledSection.from_source_target_directories(category, name,
                                        source_dir, target, files)
                sections[name] = section
    return sections
