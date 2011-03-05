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
        if o.inplace is None:
            inplace = False
        else:
            inplace = True
        if o.verbose is None:
            verbose = False
        else:
            verbose = True
        if o.jobs:
            jobs = int(o.jobs)
        else:
            jobs = None

        build_extensions = ctx.build_extensions_factory(inplace, verbose, jobs)
        build_compiled_libraries = ctx.build_compiled_libraries_factory(inplace, verbose, jobs)

        self.section_writer.sections_callbacks["compiled_libraries"] = \
                build_compiled_libraries
        self.section_writer.sections_callbacks["extensions"] = \
                build_extensions

        def build_packages(pkg):
            return _build_python_files(pkg, ctx.top_node)
        self.section_writer.sections_callbacks["pythonfiles"] = \
                build_packages

        def build_config_py(pkg):
            return _build_config_py(pkg.config_py, ctx.get_paths_scheme(), ctx.top_node)
        self.section_writer.sections_callbacks["bentofiles"] = \
                build_config_py
        self.section_writer.update_sections(ctx.pkg)

    def register_builder(self, extension_name, builder):
        """Register a builder to override the default builder for a
        given extension."""
        if extension_name in self._extension_callback:
            # Should most likely be a warning
            raise ValueError("Overriding callback: %s" % \
                             extension_name)
        if not extension_name in self.pkg.extensions:
            raise ValueError(
                    "Register callback for unknown extension: %s" % \
                    extension_name)
        self._extension_callback[extension_name] = builder

    def shutdown(self, ctx):
        self.section_writer.store(IPKG_PATH, ctx.pkg)

class SectionWriter(object):
    def __init__(self):
        callbacks = [
            ("pythonfiles", None),
            ("bentofiles", None),
            ("datafiles", build_data_files),
            ("compiled_libraries", build_distutils.build_compiled_libraries),
            ("extensions", build_distutils.build_extensions),
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

def _build_python_files(pkg, top_node):
    python_files = []
    for p in get_packages(pkg, top_node):
        python_files.extend(find_package(p, top_node))
    for m in pkg.py_modules:
        node = top_node.find_node("%s.py" % m)
        python_files.append(node.path_from(node))
    py_section = InstalledSection.from_source_target_directories("pythonfiles", "library",
            "$_srcrootdir", "$sitedir", python_files)

    return {"library": py_section}

def _config_content(paths):
    keys = sorted(paths.keys())
    n = max([len(k) for k in keys]) + 2
    content = []
    for name, value in sorted(paths.items()):
        content.append('%s = "%s"' % (name.upper().ljust(n), subst_vars(value, paths)))
    return "\n".join(content)

def _build_config_py(target, paths, top_node):
    if target is not None:
        content = _config_content(paths)
        target_node = top_node.bldnode.make_node(target)
        target_node.parent.mkdir()
        target_node.safe_write(content)

        section = InstalledSection.from_source_target_directories("bentofiles", "config",
                os.path.join("$_srcrootdir", os.path.dirname(target_node.srcpath())),
                os.path.join("$sitedir", os.path.dirname(target)),
                [os.path.basename(target)])
        return {"bentofiles": section}
    else:
        return {}

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
