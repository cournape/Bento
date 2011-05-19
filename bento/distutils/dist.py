import os

from bento.distutils.utils \
    import \
        _is_setuptools_activated
if _is_setuptools_activated():
    from setuptools \
        import \
            Distribution
else:
    from distutils.dist \
        import \
            Distribution

from bento.conv \
    import \
        pkg_to_distutils_meta
from bento.core.node \
    import \
        create_root_with_source_tree
from bento.core.package \
    import \
        PackageDescription

from bento.distutils.commands.config \
    import \
        config
from bento.distutils.commands.build \
    import \
        build
from bento.distutils.commands.install \
    import \
        install

_BENTO_MONKEYED_CLASSES = {"build": build, "config": config, "install": install}

if _is_setuptools_activated():
    from bento.distutils.commands.bdist_egg \
        import \
            bdist_egg
    _BENTO_MONKEYED_CLASSES["bdist_egg"] = bdist_egg

def _setup_cmd_classes(attrs):
    cmdclass = attrs.get("cmdclass", {})
    for klass in _BENTO_MONKEYED_CLASSES:
        if not klass in cmdclass:
            cmdclass[klass] = _BENTO_MONKEYED_CLASSES[klass]
    attrs["cmdclass"] = cmdclass
    return attrs

class BentoDistribution(Distribution):
    def __init__(self, attrs=None):
        if attrs is None:
            attrs = {}

        if not "bento_info" in attrs:
            bento_info = "bento.info"
        else:
            bento_info = attrs["bento.info"]
        self.pkg = PackageDescription.from_file(bento_info)

        attrs = _setup_cmd_classes(attrs)

        d = pkg_to_distutils_meta(self.pkg)
        attrs.update(d)

        Distribution.__init__(self, attrs)

        self.packages = self.pkg.packages
        self.py_modules = self.pkg.py_modules
        if hasattr(self, "entry_points"):
            if self.entry_points is None:
                self.entry_points = {}
            console_scripts = [e.full_representation() for e in self.pkg.executables.values()]
            if "console_scripts" in self.entry_points:
                self.entry_points["console_scripts"].extend(console_scripts)
            else:
                self.entry_points["console_scripts"] = console_scripts

        source_root = os.getcwd()
        build_root = os.path.join(source_root, "build")
        root = create_root_with_source_tree(source_root, build_root)
        self.top_node = root._ctx.srcnode
        self.build_node = root._ctx.bldnode
        self.run_node = root._ctx.srcnode

    def has_data_files(self):
        return len(self.pkg.data_files) > 0        

# Install it throughout the distutils
_MODULES = []
if _is_setuptools_activated():
    import setuptools.dist
    _MODULES.append(setuptools.dist)
import distutils.dist, distutils.core, distutils.cmd
_MODULES.extend([distutils.dist, distutils.core, distutils.cmd])
for module in _MODULES:
    module.Distribution = BentoDistribution
