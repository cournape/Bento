import os
import sys

from toydist.core.utils import \
        find_package
from toydist.core import \
        PackageDescription
from toydist.installed_package_description import \
        InstalledPkgDescription, InstalledSection

from toydist.commands.core import \
        Command, SCRIPT_NAME, UsageException
from toydist.commands.configure import \
        ConfigureState

USE_NUMPY_DISTUTILS = False

def build_extensions(extensions):
    # FIXME: import done here to avoid clashing with monkey-patch as done by
    # the convert subcommand.
    if USE_NUMPY_DISTUTILS:
        from numpy.distutils.extension import Extension
        from numpy.distutils.numpy_distribution import NumpyDistribution as Distribution
        from numpy.distutils.command.build_ext import build_ext
        from numpy.distutils.command.build_src import build_src
        from numpy.distutils.command.scons import scons
        from numpy.distutils import log
        import distutils.core
    else:
        from distutils.extension import Extension
        from distutils.dist import Distribution
        from distutils.command.build_ext import build_ext
        from distutils import log

    log.set_verbosity(1)

    dist = Distribution()
    if USE_NUMPY_DISTUTILS:
        dist.cmdclass['build_src'] = build_src
        dist.cmdclass['scons'] = scons
        distutils.core._setup_distribution = dist

    dist.ext_modules = [e for e in extensions.values()]

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
        outputs[fullname] = InstalledSection("extensions", fullname, srcdir,
                                             target, [os.path.basename(ext_target)])
    return outputs

class BuildCommand(Command):
    long_descr = """\
Purpose: build the project
Usage:   toymaker build [OPTIONS]."""
    short_descr = "build the project."

    def run(self, opts):
        self.set_option_parser()
        o, a = self.parser.parse_args(opts)
        if o.help:
            self.parser.print_help()
            return

        if not os.path.exists('.config.bin'):
            raise UsageException(
                   "You need to run %s configure before building" % SCRIPT_NAME)

        # XXX: import here because numpy import time slows down everything
        # otherwise. This is ugly, but using numpy.distutils is temporary
        # anyway
        try:
            import numpy
            USE_NUMPY_DISTUTILS = True
        except ImportError:
            USE_NUMPY_DISTUTILS = False

        s = ConfigureState.from_dump('.config.bin')

        filename = s.package_description
        scheme = dict([(k, s.paths[k]) for k in s.paths])

        pkg = PackageDescription.from_file(filename, user_flags=s.flags)

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
            sections["datafiles"][name] = InstalledSection.from_data_files(name, data_section)

        # handle extensions
        if pkg.extensions:
            extensions = build_extensions(pkg.extensions)
            sections["extension"] = extensions

        sections["executable"] = {}
        if pkg.executables:
            executables = build_executables(pkg.executables)
            for ename, evalue in executables.items():
                sections["executable"][ename] = evalue

        meta = {}
        for m in ["name", "version", "summary", "url", "author", "author_email",
                  "license", "download_url", "description", "platforms", "classifiers",
                  "install_requires"]:
            meta[m] = getattr(pkg, m)

        meta["top_levels"] = pkg.top_levels

        p = InstalledPkgDescription(sections, meta, scheme, pkg.executables)
        p.write('installed-pkg-info')

def create_script(name, module, function=None):
    sys_executable = os.path.normpath(sys.executable)
    if function is None:
        raise NotImplementedError("Generating build scripts without function not yet implemented")
    script_text = """\
#!%(python_exec)s
# TOYDIST AUTOGENERATED-CONSOLE SCRIPT
import sys
from %(module)s import %(function)s
%(function)s(sys.argv)
""" % {"python_exec": sys_executable, "module": module, "function": function}
    return script_text

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
        cnt = create_script(name, executable.module, executable.function)
        target = os.path.join(bdir, name)
        # FIXME: deal with win32 stuff here
        mode = "b"
        d = os.path.dirname(target)
        if d and not os.path.exists(d):
            os.makedirs(d)
        f = open(target, "w" + mode)
        try:
            f.write(cnt)
        finally:
            f.close()

        ret[name] = InstalledSection("executables", name, d, "$bindir",
                                     [os.path.basename(target)])
    return ret
