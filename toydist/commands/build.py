import os

from toydist.utils import \
        pprint
from toydist.cabal_parser.cabal_parser import \
        parse
from toydist.installed_package_description import \
        InstalledPkgDescription, read_installed_pkg_description

from toydist.commands.core import \
        Command
from toydist.commands.configure import \
        ConfigureState

USE_NUMPY_DISTUTILS = True

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

    for name, value in extensions.items():
        e = Extension(name, sources=value["sources"])
        dist.ext_modules = [e]

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
        source = os.path.dirname(ext_target)
        ext_descr = {'files': [os.path.basename(ext_target)],
                     'source': source,
                     'target': target}
        outputs[ext.name] = ext_descr
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
            pprint('RED', 
                   "You need to run %s configure before building" % SCRIPT_NAME)
        s = ConfigureState.from_dump('.config.bin')

        filename = s.package_description
        scheme = dict([(k, s.paths[k]) for k in s.paths])

        def find_package(pkg_name, basedir=''):
            # XXX: this function is wrong - use the code from setuptools
            pkg_dir = pkg_name.replace(".", os.path.sep)
            basedir = os.path.join(basedir, pkg_dir)
            init = os.path.join(basedir, '__init__.py')
            if not os.path.exists(init):
                raise ValueError(
                        "Missing __init__.py in package %s (in directory %s)"
                        % (pkg_name, basedir))
            return [os.path.join(basedir, f)
                        for f in
                            os.listdir(os.path.dirname(init)) if f.endswith('.py')]

        f = open(filename, 'r')
        try:
            # FIXME: root_src
            root_src = ""
            data = f.readlines()
            d = parse(data)
            library = d["library"][""]

            python_files = []
            if library.has_key('packages'):
                for p in library['packages']:
                    python_files.extend(find_package(p, root_src))
            if library.has_key('modules'):
                for m in library['modules']:
                    python_files.append(os.path.join(root_src, '%s.py' % m))

            sections = {"pythonfiles": {"files": python_files,
                                        "target": "$sitedir"}}

            # Get data files
            if d.has_key("datafiles"):
                data_sec = d["datafiles"]
                datafiles = {}
                for sec, val in data_sec.items():
                    datafiles[sec] = {
                        "files": val["files"],
                        "srcdir": val["srcdir"],
                        "target": val["target"]}
                sections["datafiles"] = datafiles

            # handle extensions
            if library.has_key("extension"):
                sections["extensions"] = build_extensions(library["extension"])

            p = InstalledPkgDescription(sections, scheme)
            p.write('installed-pkg-info')
        finally:
            f.close()
