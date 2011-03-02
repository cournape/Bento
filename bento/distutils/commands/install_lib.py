import os
import sys

from bento.distutils.utils \
    import \
        _is_setuptools_activated
if _is_setuptools_activated():
    from setuptools.command.install_lib \
        import \
            install_lib as old_install_lib
else:
    from distutils.command.install_lib \
        import \
            install_lib as old_install_lib

from bento._config \
    import \
        IPKG_PATH
from bento.core.platforms \
    import \
        get_scheme
from bento.installed_package_description \
    import \
        InstalledPkgDescription, iter_files
from bento.commands.install \
    import \
        copy_installer

class install_lib(old_install_lib):
    def __init__(self, *a, **kw):
        old_install_lib.__init__(self, *a, **kw)
        self.outfiles = []

    def initialize_options(self):
        old_install_lib.initialize_options(self)

    def finalize_options(self):
        old_install_lib.finalize_options(self)

    def run(self):
        self.run_command('build')

        ipkg = InstalledPkgDescription.from_file(IPKG_PATH)
        ipkg.update_paths({"sitedir": self.install_dir})

        file_sections = ipkg.resolve_paths()
        for kind, source, target in iter_files(file_sections):
            if kind in ["pythonfiles", "bentofiles"]:
                copy_installer(source, target, kind)
                self.outfiles.append(target)

    def get_outputs(self):
        return self.outfiles
