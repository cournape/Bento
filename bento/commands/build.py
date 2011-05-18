import os
import sys

from bento.core.utils \
    import \
        find_package, subst_vars, rename, ensure_dir
from bento.installed_package_description \
    import \
        InstalledPkgDescription, InstalledSection, ipkg_meta_from_pkg
from bento._config \
    import \
        IPKG_PATH
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

        self.section_writer.sections["pythonfiles"] = build_python_files(ctx)
        self.section_writer.sections["datafiles"] = build_data_files(ctx)
        self.section_writer.sections["executables"] = build_executables(ctx)

        ctx.compile()
        ctx.post_compile(self.section_writer)

    def shutdown(self, ctx):
        n = ctx.build_node.make_node(IPKG_PATH)
        self.section_writer.store(n.abspath(), ctx.pkg)

def build_python_files(ctx):
    py_sections = {}
    def build_py_isection(name, nodes, from_node=None):
        if from_node is None:
            from_node = ctx.top_node
        source_dir = from_node.bldpath()
        isection = InstalledSection.from_source_target_directories("pythonfiles",
            name, os.path.join("$_srcrootdir", source_dir), "$sitedir",
            [n.path_from(from_node) for n in nodes])
        py_sections[name] = isection
    for name, nodes in ctx._node_pkg.iter_category("packages"):
        build_py_isection(name, nodes)
    for name, node in ctx._node_pkg.iter_category("modules"):
        build_py_isection(name, [node])
    if ctx.pkg.config_py:
        content = _config_content(ctx.get_paths_scheme())
        target_node = ctx.build_node.make_node(ctx.pkg.config_py)
        target_node.parent.mkdir()
        target_node.safe_write(content)
        build_py_isection("bento_config", [target_node], ctx.build_node)
    return py_sections

def build_data_files(ctx):
    data_sections = {}
    for name, section in ctx._node_pkg.iter_category("datafiles"):
        source_dir = os.path.join("$_srcrootdir", section.ref_node.bldpath())
        data_sections[name] = InstalledSection.from_source_target_directories("datafiles", name,
            source_dir, section.target_dir, [n.path_from(section.ref_node) for n in section.nodes])
    return data_sections

def build_executables(ctx):
    scripts_node = ctx.build_node.make_node("scripts-%s" % sys.version[:3])
    scripts_node.mkdir()
    executable_sections = {}
    for name, executable in ctx.pkg.executables.iteritems():
        section = build_executable(name, executable, scripts_node)
        executable_sections[name] = section
    return executable_sections

def build_isection(bld, ext_name, files, category):
    """Build an InstalledSection from the list of files for an
    extension/compiled library.

    files are expected to be given relatively to build_node."""
    # TODO: make this function common between all builders (distutils, yaku, etc...)
    if len(files) < 1:
        return InstalledSection.from_source_target_directories(category, ext_name,
            "", "", files)

    # FIXME: do package -> location translation correctly
    pkg_dir = os.path.dirname(ext_name.replace('.', os.path.sep))
    target_dir = os.path.join('$sitedir', pkg_dir)

    # FIXME: this assumes every file in outputs are in one single directory
    nodes = []
    for f in files:
        n = bld.build_node.find_node(f)
        if n is None:
            raise IOError("file %s not found (relatively to %s)" % (f, bld.build_node.abspath()))
        else:
            nodes.append(n)
    source_dir = nodes[0].parent
    section = InstalledSection.from_source_target_directories(category, ext_name,
        os.path.join("$_srcrootdir", source_dir.bldpath()),
        target_dir, [o.path_from(source_dir) for o in nodes])
    return section

class SectionWriter(object):
    def __init__(self):
        self.sections = {}

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

def build_executable(name, executable, scripts_node):
    if sys.platform == "win32":
        nodes = create_win32_script(name, executable, scripts_node)
    else:
        nodes = create_posix_script(name, executable, scripts_node)
    return InstalledSection.from_source_target_directories(
            "executables", name, os.path.join("$_srcrootdir", scripts_node.bldpath()),
            "$bindir", [n.path_from(scripts_node) for n in nodes])
