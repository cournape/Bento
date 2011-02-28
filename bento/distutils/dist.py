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

from bento.core.node \
    import \
        Node
from bento.core.package \
    import \
        PackageDescription

class BentoDistribution(Distribution):
    def __init__(self, *a, **kw):
        Distribution.__init__(self, *a, **kw)

        self.pkg = PackageDescription.from_file("bento.info")
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

        self.root_node = Node("", None)
        self.top_node = self.root_node.find_dir(os.getcwd())
