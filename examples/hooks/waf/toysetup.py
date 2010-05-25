from cStringIO import StringIO
from cPickle import dump, load
import os, sys

from toydist.core.utils \
    import \
        pprint
from toydist.commands.configure \
    import \
        get_configured_state
from toydist.commands.hooks \
    import \
        override, post_configure

# FIXME: ugly as hell
IMPORT_DICT = {}

join = os.path.join

def _init():
    global IMPORT_DICT

    wafdir = os.getcwd()
    w = join(wafdir, 'wafadmin')
    t = join(w, 'Tools')
    f = join(w, '3rdparty')
    sys.path = [w, t, f] + sys.path

    import Configure
    import Utils, Options, Build
    import Environment

    cwd = os.getcwd()
    opt_obj = Options.Handler()
    opt_obj.curdir = cwd
    opt_obj.tool_options('compiler_cc')
    opt_obj.parse_args([])
    Options.tooldir = [t]

    class foo(object):
       pass
    Utils.g_module = foo
    Utils.g_module.root_path = cwd

    Options.lockfile = ".waf.lock"
    CACHEDIR = "c4che"

    IMPORT_DICT["Configure"] = Configure
    IMPORT_DICT["Build"] = Build
    IMPORT_DICT["Options"] = Options
    IMPORT_DICT["cwd"] = cwd
    IMPORT_DICT["CACHEDIR"] = CACHEDIR
    IMPORT_DICT["Environment"] = Environment

def startup():
    _init()

@post_configure
def configure_waf():
    pprint('BLUE', "Configuring waf")
    Configure = IMPORT_DICT["Configure"]
    cwd = IMPORT_DICT["cwd"]
    CACHEDIR = IMPORT_DICT["CACHEDIR"]
    Options = IMPORT_DICT["Options"]

    conf_log = open("config.log", "w")
    ctx = Configure.ConfigurationContext()
    ctx.log = conf_log
    ctx.srcdir = cwd
    ctx.blddir = join(cwd, 'build')
    ctx.check_tool('compiler_cc')
    ctx.check_tool('python')
    ctx.check_python_version((2, 4, 0))
    ctx.check_python_headers()
    ctx.cachedir = CACHEDIR
    #ctx.check_cc(fragment='int main() {return 0;}')
    ctx.store()

    ctx.env.store(Options.lockfile)

def ext_name_to_path(name):
    """Convert extension name to path - the path does not include the
    file extension

    Example: foo.bar -> foo/bar
    """
    return name.replace('.', os.path.sep)

@override
def build(opts):
    pprint('BLUE', "Overriden build command")
    Environment = IMPORT_DICT["Environment"]
    Options = IMPORT_DICT["Options"]
    Build = IMPORT_DICT["Build"]
    CACHEDIR = IMPORT_DICT["CACHEDIR"]
    cwd = IMPORT_DICT["cwd"]

    env = Environment.Environment(Options.lockfile)

    bld = Build.BuildContext()
    bld.cachedir = CACHEDIR
    bld.load()

    bld.all_envs['default'] = env
    bld.lst_variants = bld.all_envs.keys()
    bld.load_dirs(cwd, join(cwd, 'build'))

    config = get_configured_state()
    pkg = config.pkg
    for ext in pkg.extensions.values():
        target = ext.name.replace(".", os.sep)
        dirname = os.path.dirname(target)
        parent_node = bld.path.ensure_dir_node_from_path(dirname)
        bld.rescan(parent_node)
        bld(features='cc cshlib pyext', source=ext.sources, target=target)
    bld.compile()

    from toydist.commands.build \
        import build_python_files, \
            build_data_files, build_executables
    from toydist.installed_package_description \
        import \
            InstalledPkgDescription, InstalledSection, \
            ipkg_meta_from_pkg
    outputs = get_build_products(bld)

    s = get_configured_state()
    scheme = dict([(k, s.paths[k]) for k in s.paths])
    pkg = s.pkg

    sections = {
            "pythonfiles": {},
            "datafiles": {},
            "extension": {},
            "executable": {}
    }

    def build_extensions(pkg):
        ret = {}
        for e in pkg.extensions.values():
            targets = outputs[e.name]
            source_dir = os.path.dirname(targets[0])
            fullname = os.path.basename(targets[0])
            pkg_dir = os.path.dirname(ext_name_to_path(e.name))
            install_dir = os.path.join('$sitedir', pkg_dir)
            section = InstalledSection("extensions", 
                    fullname, source_dir, install_dir,
                    [os.path.basename(t) for t in targets])
            ret[fullname] = section
        return ret

    sections["pythonfiles"].update(build_python_files(pkg))
    sections["datafiles"].update(build_data_files(pkg))
    sections["extension"].update(build_extensions(pkg))
    sections["executable"].update(build_executables(pkg))

    meta = ipkg_meta_from_pkg(pkg)
    p = InstalledPkgDescription(sections, meta, scheme,
                                pkg.executables)
    p.write('installed-pkg-info')

def get_build_products(bld):
    outputs = {}
    for target in bld.all_task_gen:
        try:
            link_task = target.link_task
            name = target.name.replace(os.sep, ".")
            outputs[name] = [o.abspath(target.env) for o in link_task.outputs]
        except AttributeError:
            pass

    return outputs
