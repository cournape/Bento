import os
import errno

from bento.core.utils \
    import \
        extract_exception
from bento.compat.api \
    import \
        relpath
from bento.installed_package_description \
    import \
        InstalledSection
from bento.commands.errors \
    import \
        CommandExecutionFailure

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

    def _setup_cmd(self, cmd, t):
        from distutils.ccompiler import new_compiler
        from distutils.sysconfig import customize_compiler
        from distutils.command.build import build

        build = self._dist.get_command_obj("build")
        bld_cmd = build.get_finalized_command(cmd)

        compiler = new_compiler(compiler=bld_cmd.compiler,
                                dry_run=bld_cmd.dry_run,
                                force=bld_cmd.force)
        customize_compiler(compiler)
        return bld_cmd, compiler

    def _setup_clib(self):
        from distutils.command.build_clib import build_clib
        return self._setup_cmd("build_clib", "compiled_libraries")

    def _setup_ext(self):
        from distutils.command.build_ext import build_ext
        return self._setup_cmd("build_ext", "extensions")

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

        dist = self._dist
        dist.ext_modules = [toyext_to_distext(extension)]

        bld_cmd, compiler = self._setup_ext()
        try:
            bld_cmd.run()

            base, filename = os.path.split(self._extension_filename(extension.name, bld_cmd))
            fullname = os.path.join(bld_cmd.build_lib, base, filename)
            return [relpath(fullname, self._build_base)]
        except distutils.errors.DistutilsError:
            e = extract_exception()
            raise BuildError(str(e))

    def build_compiled_library(self, library):
        import distutils.errors

        dist = self._dist
        dist.libraries = [to_dist_compiled_library(library)]

        bld_cmd, compiler = self._setup_clib()
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
                bld_cmd.run()

                return [relpath(target, self._build_base)]
            except distutils.errors.DistutilsError:
                e = extract_exception()
                raise BuildError(str(e))
        finally:
            bld_cmd.build_clib = old_build_clib
