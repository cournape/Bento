import os
import sys

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
from waflib.Configure \
    import \
        ConfigurationContext
from waflib import Options
from waflib import Context
from waflib import Logs
from waflib import Build

from bento.commands.context \
    import \
        ConfigureContext, BuildContext
from bento.core.subpackage \
    import \
        get_extensions
from bento.installed_package_description \
    import \
        InstalledSection

WAF_TOP = os.path.join(WAFDIR, os.pardir)

WAF_CONFIG_LOG = 'config.log'

# FIXME: _init should be run and and only once per bentomaker invocation
__HAS_RUN = False
def _init():
    global __HAS_RUN
    if __HAS_RUN:
        return
    else:
        __HAS_RUN = True

    tooldir = os.path.join(WAFDIR, "Tools")

    sys.path.insert(0, tooldir)
    cwd = os.getcwd()

    Logs.init_log()

    class FakeModule(object):
        pass
    Context.g_module = FakeModule
    Context.g_module.root_path = os.path.abspath(__file__)
    Context.g_module.top = os.getcwd()
    Context.g_module.out = os.path.join(os.getcwd(), "build")

    Context.top_dir = os.getcwd()
    Context.out_dir = os.path.join(os.getcwd(), "build")
    Context.waf_dir = WAF_TOP

    opts = OptionsContext()
    opts.parse_args([])
    opts.load("compiler_c")
    Options.options.check_c_compiler = "gcc"

class ConfigureWafContext(ConfigureContext):
    def __init__(self, cmd, cmd_argv, options_context, pkg, top_node):
        super(ConfigureWafContext, self).__init__(cmd, cmd_argv, options_context, pkg, top_node)

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

def ext_name_to_path(name):
    """Convert extension name to path - the path does not include the
    file extension

    Example: foo.bar -> foo/bar
    """
    return name.replace('.', os.path.sep)

class BuildWafContext(BuildContext):
    def __init__(self, cmd, cmd_argv, options_context, pkg, top_node):
        super(BuildWafContext, self).__init__(cmd, cmd_argv, options_context, pkg, top_node)

        _init()
        waf_context = create_context("build")
        waf_context.restore()
        if not waf_context.all_envs:
            waf_context.load_envs()
        self.waf_context = waf_context

    def build_extensions_factory(self, *a, **kw):
        def builder(pkg):
            bld = self.waf_context
            for name, extension in get_extensions(pkg, self.top_node).iteritems():
                print ext_name_to_path(extension.name)
                bld(features='c cshlib pyext', source=extension.sources,
                    target=ext_name_to_path(extension.name))
            bld.compile()
            return build_installed_sections(bld)
        return builder

    def build_compiled_libraries_factory(self, *a, **kw):
        def builder(pkg):
            if len(self.pkg.compiled_libraries) > 0:
                raise NotImplementedError("waf mode for compiled " \
                                          "libraries not yet implemented")
            return {}
        return builder

def build_installed_sections(bld):
    sections = {}
    for group in bld.groups:
        for task_gen in group:
            if hasattr(task_gen, "link_task"):
                name = task_gen.name.replace(os.sep, ".")
                pkg_dir = os.path.dirname(task_gen.name)
                source_dir = task_gen.link_task.outputs[0].parent.path_from(bld.srcnode)
                target = os.path.join("$sitedir", pkg_dir)
                files = [o.name for o in task_gen.link_task.outputs]

                section = InstalledSection.from_source_target_directories("extensions", name,
                                        source_dir, target, files)
                sections[name] = section
    return sections
