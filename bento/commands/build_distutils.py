import os
import errno

from bento.utils.utils \
    import \
        extract_exception
from bento.compat.api \
    import \
        relpath
from bento.installed_package_description \
    import \
        InstalledSection
from bento.errors \
    import \
        CommandExecutionFailure

import bento.errors

def toyext_to_distext(e):
    """Convert a bento Extension instance to a distutils
    Extension."""
    # FIXME: this is temporary, will be removed once we do not depend
    # on distutils to build extensions anymore. That's why this is not
    # a method of the bento Extension class.
    from distutils.extension import Extension as DistExtension
    return DistExtension(e.name, sources=[s for s in e.sources],
                         include_dirs=[inc for inc in e.include_dirs])

def to_dist_compiled_library(library):
    name = module_to_path(library.name)
    return (os.path.basename(name), dict(sources=library.sources))

def module_to_path(module):
    return module.replace(".", os.path.sep)

class DistutilsBuilder(object):
    def __init__(self, verbosity=1, build_base=None):
        from distutils.dist import Distribution
        from distutils import log

        log.set_verbosity(verbosity)

        self._dist = Distribution()
        self._compilers = {}
        self._cmds = {}

        if build_base:
            opt_dict = self._dist.get_option_dict("build")
            opt_dict["build_base"] = ("bento", build_base)
        build = self._dist.get_command_obj("build")
        self._build_base = build.build_base

        self.ext_bld_cmd = self._setup_build_ext()
        self.clib_bld_cmd = self._setup_build_clib()

    def _setup_build_ext(self):
        # Horrible hack to initialize build_ext: build_ext initialization is
        # partially done within the run function (!), and is bypassed if no
        # extensions is available. We fake it just enough so that run does all
        # the initialization without trying to actually build anything.
        build = self._dist.get_command_obj("build")
        bld_cmd = build.get_finalized_command("build_ext")
        bld_cmd.initialize_options()
        bld_cmd.finalize_options()
        old_build_extensions = bld_cmd.build_extensions
        try:
            bld_cmd.build_extensions = lambda: None
            bld_cmd.extensions = [None]
            bld_cmd.run()
        finally:
            bld_cmd.build_extensions = old_build_extensions

        return bld_cmd

    def _setup_build_clib(self):
        # Horrible hack to initialize build_ext: build_ext initialization is
        # partially done within the run function (!), and is bypassed if no
        # extensions is available. We fake it just enough so that run does all
        # the initialization without trying to actually build anything.
        build = self._dist.get_command_obj("build")
        bld_cmd = build.get_finalized_command("build_clib")
        bld_cmd.initialize_options()
        bld_cmd.finalize_options()
        old_build_libraries = bld_cmd.build_libraries
        try:
            bld_cmd.build_libraries = lambda ignored: None
            bld_cmd.libraries = [None]
            bld_cmd.run()
        finally:
            bld_cmd.build_libraries = old_build_libraries

        return bld_cmd

    def _extension_filename(self, name, cmd):
        m = module_to_path(name)
        d, b = os.path.split(m)
        return os.path.join(d, cmd.get_ext_filename(b))

    def _compiled_library_filename(self, name, compiler):
        m = module_to_path(name)
        d, b = os.path.split(m)
        return os.path.join(d, compiler.library_filename(b))

    def build_extension(self, extension):
        import distutils.errors

        dist_extension = toyext_to_distext(extension)

        bld_cmd = self.ext_bld_cmd
        try:
            bld_cmd.build_extension(dist_extension)

            base, filename = os.path.split(self._extension_filename(dist_extension.name, bld_cmd))
            fullname = os.path.join(bld_cmd.build_lib, base, filename)
            return [relpath(fullname, self._build_base)]
        except distutils.errors.DistutilsError:
            e = extract_exception()
            raise BuildError(str(e))

    def build_compiled_library(self, library):
        import distutils.errors

        bld_cmd = self.clib_bld_cmd
        compiler = bld_cmd.compiler
        base, filename = os.path.split(self._compiled_library_filename(library.name, compiler))
        old_build_clib = bld_cmd.build_clib
        if base:
            # workaround for a distutils issue: distutils put all C libraries
            # in the same directory, and we cannot control the output directory
            # from the name - we need to hack build_clib directory
            bld_cmd.build_clib = os.path.join(old_build_clib, base)
        try:
            try:
                # workaround for yet another bug in distutils: distutils fucks up when
                # building a static library if the target alread exists on at least mac
                # os x.
                target = os.path.join(old_build_clib, base, filename)
                try:
                    os.remove(target)
                except OSError:
                    e = extract_exception()
                    if e.errno != errno.ENOENT:
                        raise
                build_info = {"sources": library.sources,
                        "include_dirs": library.include_dirs}
                bld_cmd.build_libraries([(library.name, build_info)])

                return [relpath(target, self._build_base)]
            except distutils.errors.DistutilsError:
                e = extract_exception()
                raise bento.errors.BuildError(str(e))
        finally:
            bld_cmd.build_clib = old_build_clib
