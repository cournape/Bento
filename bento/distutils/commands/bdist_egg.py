import os

from bento.distutils.utils \
    import \
        _is_setuptools_activated
if _is_setuptools_activated():
    from setuptools.command.bdist_egg \
        import \
            bdist_egg as old_bdist_egg
else:
    raise ValueError("You cannot use bdist_egg without setuptools enabled first")

from bento._config \
    import \
        IPKG_PATH
from bento.installed_package_description \
    import \
        InstalledPkgDescription
from bento.commands.build_egg \
    import \
        build_egg

class bdist_egg(old_bdist_egg):
    def __init__(self, *a, **kw):
        old_bdist_egg.__init__(self, *a, **kw)

    def initialize_options(self):
        old_bdist_egg.initialize_options(self)

    def finalize_options(self):
        old_bdist_egg.finalize_options(self)

    def run(self):

        build = self.get_finalized_command("build")
        build.run()
        ipkg = InstalledPkgDescription.from_file(IPKG_PATH)
        build_egg(ipkg)
