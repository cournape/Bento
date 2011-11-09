def monkey_patch():
    # XXX: keep the import here to avoid any side-effects from mere import of
    # bento.distutils
    from bento.distutils.utils \
        import \
            _is_setuptools_activated
    import bento.distutils.dist

    # Install it throughout the distutils
    _MODULES = []
    if _is_setuptools_activated():
        import setuptools.dist
        _MODULES.append(setuptools.dist)
    import distutils.dist, distutils.core, distutils.cmd
    _MODULES.extend([distutils.dist, distutils.core, distutils.cmd])
    for module in _MODULES:
        module.Distribution = bento.distutils.dist.BentoDistribution
