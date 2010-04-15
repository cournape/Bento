import os
import sys

from toydist.core.utils import \
        find_package
from toydist.installed_package_description import \
        InstalledPkgDescription, InstalledSection

from toydist.commands.errors \
    import \
        UsageException
from toydist.commands.core import \
        Command, SCRIPT_NAME
from toydist.commands.configure import \
        ConfigureState, get_configured_state
from toydist.commands.script_utils import \
        create_posix_script, create_win32_script

__USE_NUMPY_DISTUTILS = False

def toyext_to_distext(e):
    """Convert a toydist Extension instance to a distutils
    Extension."""
    # FIXME: this is temporary, will be removed once we do not depend
    # on distutils to build extensions anymore. That's why this is not
    # a method of the toydist Extension class.
    from distutils.extension import Extension as DistExtension
    return DistExtension(e.name, sources=[s for s in e.sources],
                         include_dirs=[inc for inc in e.include_dirs])

def build_extensions(extensions, use_numpy_distutils):
    # FIXME: import done here to avoid clashing with monkey-patch as done by
    # the convert subcommand.
    if use_numpy_distutils:
        from numpy.distutils.numpy_distribution \
            import \
                NumpyDistribution as Distribution
        from numpy.distutils.command.build_ext \
            import \
                build_ext
        from numpy.distutils.command.build_src \
            import \
                build_src
        from numpy.distutils.command.scons \
            import \
                scons
        from numpy.distutils import log
        import distutils.core
    else:
        from distutils.dist \
            import \
                Distribution
        from distutils.command.build_ext \
            import \
                build_ext
        from distutils import log

    log.set_verbosity(1)

    dist = Distribution()
    if use_numpy_distutils:
        dist.cmdclass['build_src'] = build_src
        dist.cmdclass['scons'] = scons
        distutils.core._setup_distribution = dist

    dist.ext_modules = [toyext_to_distext(e) for e in
                            extensions.values()]

    bld_cmd = build_ext(dist)
    bld_cmd.initialize_options()
    bld_cmd.finalize_options()
    bld_cmd.run()

    outputs = {}
    for ext in bld_cmd.extensions:
        # FIXME: do package -> location translation correctly
        pkg_dir = os.path.dirname(ext.name.replace('.', os.path.sep))
        target = os.path.join('$sitedir', pkg_dir)
        fullname = bld_cmd.get_ext_fullname(ext.name)
        ext_target = os.path.join(bld_cmd.build_lib,
                                 bld_cmd.get_ext_filename(fullname))
        srcdir = os.path.dirname(ext_target)
        section = InstalledSection("extensions", fullname, srcdir,
                                    target, [os.path.basename(ext_target)])
        outputs[fullname] = section
    return outputs

class BuildCommand(Command):
    long_descr = """\
Purpose: build the project
Usage:   toymaker build [OPTIONS]."""
    short_descr = "build the project."

    def run(self, opts):
        global __USE_NUMPY_DISTUTILS

        self.set_option_parser()
        o, a = self.parser.parse_args(opts)
        if o.help:
            self.parser.print_help()
            return

        # XXX: import here because numpy import time slows down everything
        # otherwise. This is ugly, but using numpy.distutils is temporary
        # anyway
        try:
            import numpy
            __USE_NUMPY_DISTUTILS = True
        except ImportError:
            __USE_NUMPY_DISTUTILS = False

        s = get_configured_state()

        pkg = s.pkg
        scheme = dict([(k, s.paths[k]) for k in s.paths])


        # FIXME: root_src
        root_src = ""
        python_files = []
        for p in pkg.packages:
            python_files.extend(find_package(p, root_src))
        for m in pkg.py_modules:
            python_files.append(os.path.join(root_src, '%s.py' % m))

        sections = {"pythonfiles": {"library":
                    InstalledSection("pythonfiles", "library", root_src,
                                     "$sitedir", python_files)}}

        # Get data files
        sections["datafiles"] = {}
        for name, data_section in pkg.data_files.items():
            data_section.files = data_section.resolve_glob()
            sections["datafiles"][name] = \
                    InstalledSection.from_data_files(name, data_section)

        # handle extensions
        if pkg.extensions:
            extensions = build_extensions(pkg.extensions, __USE_NUMPY_DISTUTILS)
            sections["extension"] = extensions

        sections["executable"] = {}
        if pkg.executables:
            executables = build_executables(pkg.executables)
            for ename, evalue in executables.items():
                sections["executable"][ename] = evalue

        meta = {}
        for m in ["name", "version", "summary", "url", "author",
                  "author_email", "license", "download_url", "description",
                  "platforms", "classifiers", "install_requires"]:
            meta[m] = getattr(pkg, m)

        meta["top_levels"] = pkg.top_levels

        p = InstalledPkgDescription(sections, meta, scheme, pkg.executables)
        p.write('installed-pkg-info')

def build_dir():
    # FIXME: handle build directory differently, wo depending on distutils
    from distutils.command.build_scripts import build_scripts
    from distutils.dist import Distribution

    dist = Distribution()

    bld_scripts = build_scripts(dist)
    bld_scripts.initialize_options()
    bld_scripts.finalize_options()
    return bld_scripts.build_dir

def build_executables(executables):
    bdir = build_dir()
    ret = {}

    for name, executable in executables.items():
        if sys.platform == "win32":
            ret[name] = create_win32_script(name, executable, bdir)
        else:
            ret[name] = create_posix_script(name, executable, bdir)
    return ret
