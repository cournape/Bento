import os

from bento.distutils.utils \
    import \
        _is_setuptools_activated
if _is_setuptools_activated():
    from setuptools.command.sdist \
        import \
            sdist as old_sdist
else:
    from distutils.command.sdist \
        import \
            sdist as old_sdist
from distutils.filelist \
    import \
        FileList

from bento._config \
    import \
        BENTO_SCRIPT
from bento.core.node \
    import \
        Node
from bento.core.package \
    import \
        file_list, PackageDescription

class sdist(old_sdist):
    def __init__(self, *a, **kw):
        old_sdist.__init__(self, *a, **kw)
        self.root = Node("", None)
        self.top = self.root.find_dir(os.getcwd())

    def initialize_options(self):
        old_sdist.initialize_options(self)

    def finalize_options(self):
        old_sdist.finalize_options(self)

    def run(self):
        pkg = PackageDescription.from_file(BENTO_SCRIPT)
        self.filelist = FileList()
        self.filelist.files = file_list(pkg, self.top)

        if self.manifest_only:
            return
        self.make_distribution()
