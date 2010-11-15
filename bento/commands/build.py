import os
import sys

from bento.core.utils import \
        find_package, OrderedDict, subst_vars, rename, ensure_dir
from bento.installed_package_description import \
        InstalledPkgDescription, InstalledSection, ipkg_meta_from_pkg
from bento._config \
    import \
        IPKG_PATH, BUILD_DIR
from bento.core.subpackage \
    import \
        get_extensions, get_compiled_libraries, get_packages

from bento.commands.configure \
    import \
        get_configured_state
from bento.commands.core \
    import \
        Option
from bento.commands \
    import \
        build_distutils
from bento.commands \
    import \
        build_yaku
from bento.commands.core import \
        Command
from bento.commands.script_utils import \
        create_posix_script, create_win32_script

class BuildCommand(Command):
    long_descr = """\
Purpose: build the project
Usage:   bentomaker build [OPTIONS]."""
    short_descr = "build the project."
    opts = Command.opts + [Option("-i", "--inplace",
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
        self.build_type = None

    def run(self, ctx):
        opts = ctx.cmd_opts
        o, a = self.parser.parse_args(opts)
        if o.help:
            self.parser.print_help()
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

        extensions = get_extensions(ctx.pkg, ctx.top_node)
        libraries = get_compiled_libraries(ctx.pkg, ctx.top_node)

        if ctx.get_user_data()["use_distutils"]:
            self.build_type = "distutils"
            build_extensions = build_distutils.build_extensions
        else:
            self.build_type = "yaku"
            def builder(pkg):
                return build_yaku.build_extensions(extensions,
                        ctx.yaku_build_ctx, ctx._extensions_callback,
                        ctx._extension_envs, inplace, verbose, jobs)
            build_extensions = builder

            def builder(pkg):
                return build_yaku.build_compiled_libraries(libraries,
                        ctx.yaku_build_ctx, ctx._clibraries_callback,
                        ctx._clibrary_envs, inplace, verbose, jobs)
            build_compiled_libraries = builder

        self.section_writer.sections_callbacks["compiled_libraries"] = \
                build_compiled_libraries
        self.section_writer.sections_callbacks["extensions"] = \
                build_extensions

        def build_packages(pkg):
            return _build_python_files(pkg, ctx.top_node)
        self.section_writer.sections_callbacks["pythonfiles"] = \
                build_packages
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
            ("bentofiles", build_bento_files),
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

def build_bento_files(pkg):
    s = get_configured_state()
    scheme = s.paths
    if pkg.config_py is not None:
        tmp_config = os.path.join(BUILD_DIR, "__tmp_config.py")
        fid = open(tmp_config, "w")
        try:
            for name, value in scheme.items():
                fid.write('%s = "%s"\n' % (name.upper(), subst_vars(value, scheme)))
        finally:
            fid.close()
        target = os.path.join(os.path.dirname(tmp_config),
                              pkg.config_py)
        ensure_dir(target)
        rename(tmp_config, target)

        section = InstalledSection.from_source_target_directories("bentofiles", "config",
                os.path.join("$_srcrootdir", BUILD_DIR),
                "$sitedir", [pkg.config_py])
        return {"bentofiles": section}
    else:
        return {}

def build_data_files(pkg):
    ret = {}
    # Get data files
    for name, data_section in pkg.data_files.items():
        data_section.files = data_section.resolve_glob()
        data_section.source_dir = os.path.join("$_srcrootdir", data_section.source_dir)
        ret[name] = InstalledSection.from_data_files(name, data_section)

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
