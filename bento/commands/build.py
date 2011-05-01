import os
import sys

from bento.core.utils \
    import \
        find_package, OrderedDict, subst_vars, rename, ensure_dir
from bento.installed_package_description \
    import \
        InstalledPkgDescription, InstalledSection, ipkg_meta_from_pkg
from bento._config \
    import \
        IPKG_PATH, BUILD_DIR
from bento.core.subpackage \
    import \
        get_extensions, get_compiled_libraries, get_packages
from bento.core.pkg_objects \
    import \
        DataFiles

from bento.commands.core \
    import \
        Option
from bento.commands \
    import \
        build_distutils
from bento.commands \
    import \
        build_yaku
from bento.commands.core \
    import \
        Command
from bento.commands.script_utils \
    import \
        create_posix_script, create_win32_script

def build_isection(bld, ext_name, files, category):
    """Build an InstalledSection from the list of files for an
    extension/compiled library.

    files are expected to be given relatively to top_node."""
    # TODO: make this function common between all builders (distutils, yaku, etc...)
    if len(files) < 1:
        return InstalledSection.from_source_target_directories(category, ext_name,
            "", "", files)

    # FIXME: do package -> location translation correctly
    pkg_dir = os.path.dirname(ext_name.replace('.', os.path.sep))
    target = os.path.join('$sitedir', pkg_dir)

    # FIXME: this assumes every file in outputs are in one single directory
    nodes = []
    for f in files:
        # FIXME: change internal context APIs to return built files relatively
        # to build directory
        n = bld.top_node.bldnode.parent.find_node(f)
        if n is None:
            raise IOError("file %s not found (relatively to %s)" % (f, bld.path.abspath()))
        else:
            nodes.append(n)
    srcdir = nodes[0].parent.path_from(bld.top_node)
    section = InstalledSection.from_source_target_directories(category, ext_name, srcdir,
                                target, [o.name for o in nodes])
    return section

class BuildCommand(Command):
    long_descr = """\
Purpose: build the project
Usage:   bentomaker build [OPTIONS]."""
    short_descr = "build the project."
    common_options = Command.common_options \
                        + [Option("-i", "--inplace",
                                  help="Build extensions in place", action="store_true"),
                           Option("-j", "--jobs",
                                  help="Parallel builds (yaku build only - EXPERIMENTAL)",
                                  dest="jobs"),
                           Option("-v", "--verbose",
                                  help="Verbose output (yaku build only)",
                                  action="store_true")]

    @classmethod
    def has_run(self):
        return os.path.exists(IPKG_PATH)

    def __init__(self, *a, **kw):
        Command.__init__(self, *a, **kw)
        self.section_writer = SectionWriter()

    def run(self, ctx):
        argv = ctx.get_command_arguments()
        p = ctx.options_context.parser
        o, a = p.parse_args(argv)
        if o.help:
            p.print_help()
            return

        py_sections = {}
        def build_py_isection(name, nodes):
            isection = InstalledSection.from_source_target_directories("pythonfiles",
                name, "$_srcrootdir", "$sitedir", [n.srcpath() for n in nodes])
            py_sections[name] = isection
        for name, nodes in ctx._node_pkg.iter_category("packages"):
            build_py_isection(name, nodes)
        for name, node in ctx._node_pkg.iter_category("modules"):
            build_py_isection(name, [node])
        if ctx.pkg.config_py:
            content = _config_content(ctx.get_paths_scheme())
            target_node = ctx.top_node.bldnode.make_node(ctx.pkg.config_py)
            target_node.parent.mkdir()
            target_node.safe_write(content)
            build_py_isection("bento_config", [target_node])
        self.section_writer.sections["pythonfiles"] = py_sections

        self.section_writer.update_sections(ctx.pkg)
        ctx.compile()
        ctx.post_compile(self.section_writer)

    def shutdown(self, ctx):
        self.section_writer.store(IPKG_PATH, ctx.pkg)

class SectionWriter(object):
    def __init__(self):
        callbacks = [
            ("datafiles", build_data_files),
            ("executables", build_executables)]
        self.sections_callbacks = OrderedDict(callbacks)
        self.sections = {}
        for k in self.sections_callbacks:
            self.sections[k] = {}

    def update_sections(self, pkg):
        for name, updater in self.sections_callbacks.iteritems():
            self.sections[name].update(updater(pkg))

    def store(self, filename, pkg):
        meta = ipkg_meta_from_pkg(pkg)
        p = InstalledPkgDescription(self.sections, meta, pkg.executables)
        p.write(filename)

def _config_content(paths):
    keys = sorted(paths.keys())
    n = max([len(k) for k in keys]) + 2
    content = []
    for name, value in sorted(paths.items()):
        content.append('%s = "%s"' % (name.upper().ljust(n), subst_vars(value, paths)))
    return "\n".join(content)

def build_data_files(pkg):
    ret = {}
    # Get data files
    for name, data_section in pkg.data_files.items():
        files = data_section.resolve_glob()
        source_dir = os.path.join("$_srcrootdir", data_section.source_dir)
        new_data_section = DataFiles(data_section.name, files,
                                     data_section.target_dir, source_dir)
        ret[name] = InstalledSection.from_data_files(name, new_data_section)

    return ret

def build_dir():
    # FIXME: handle build directory differently, wo depending on distutils
    from distutils.command.build_scripts import build_scripts
    from distutils.dist import Distribution

    dist = Distribution()

    bld_scripts = build_scripts(dist)
    bld_scripts.initialize_options()
    bld_scripts.finalize_options()
    return bld_scripts.build_dir

def build_executables(pkg):
    if not pkg.executables:
        return {}
    bdir = build_dir()
    ret = {}

    for name, executable in pkg.executables.items():
        if sys.platform == "win32":
            ret[name] = create_win32_script(name, executable, bdir)
        else:
            ret[name] = create_posix_script(name, executable, bdir)
    return ret
