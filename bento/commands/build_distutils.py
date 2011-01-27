import os

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

def build_extensions(pkg):
    if not pkg.extensions:
        return {}

    # XXX: import here because numpy import time slows down everything
    # otherwise. This is ugly, but using numpy.distutils is temporary
    # anyway
    try:
        import numpy
        use_numpy_distutils = True
    except ImportError:
        use_numpy_distutils = False

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
    import distutils.errors

    log.set_verbosity(1)

    dist = Distribution()
    if use_numpy_distutils:
        dist.cmdclass['build_src'] = build_src
        dist.cmdclass['scons'] = scons
        distutils.core._setup_distribution = dist

    dist.ext_modules = [toyext_to_distext(e) for e in
                        pkg.extensions.values()]

    try:
        bld_cmd = build_ext(dist)
        bld_cmd.initialize_options()
        bld_cmd.finalize_options()
        bld_cmd.run()

        ret = {}
        for ext in bld_cmd.extensions:
            # FIXME: do package -> location translation correctly
            pkg_dir = os.path.dirname(ext.name.replace('.', os.path.sep))
            target = os.path.join('$sitedir', pkg_dir)
            fullname = bld_cmd.get_ext_fullname(ext.name)
            ext_target = os.path.join(bld_cmd.build_lib,
                                     bld_cmd.get_ext_filename(fullname))
            srcdir = os.path.dirname(ext_target)
            section = InstalledSection.from_source_target_directories("extensions", fullname,
                                    srcdir, target, [os.path.basename(ext_target)])
            ret[fullname] = section
        return ret
    except distutils.errors.DistutilsError, e:
        raise CommandExecutionFailure(str(e))

def build_compiled_libraries(pkg):
    if len(pkg.compiled_libraries) > 0:
        raise NotImplementedError("distutils mode for compiled " \
                                  "libraries not yet implemented")
    return {}
