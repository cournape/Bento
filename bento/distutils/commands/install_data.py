import os
import sys

from distutils.command.install_data \
    import \
        install_data as old_install_data

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

class install_data(old_install_data):
    def __init__(self, *a, **kw):
        old_install_data.__init__(self, *a, **kw)

    def initialize_options(self):
        old_install_data.initialize_options(self)

    def finalize_options(self):
        old_install_data.finalize_options(self)

    def run(self):
        self.run_command('build')

        ipkg = InstalledPkgDescription.from_file(IPKG_PATH)
        ipkg.update_paths({"prefix": self.install_dir, "eprefix": self.install_dir})

        file_sections = ipkg.resolve_paths()
        for kind, source, target in iter_files(file_sections):
            if kind in ["datafiles"]:
                copy_installer(source, target, kind)
                self.outfiles.append(target)
