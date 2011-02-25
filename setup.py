import shutil
import os
import subprocess
import re

from os.path \
    import \
        join, basename, dirname
from glob \
    import \
        glob

import setuptools
from setuptools.command.install \
    import \
        install as old_install
from distutils.core \
    import \
        setup
from distutils.filelist \
    import \
        FileList

from bento.core \
    import \
        PackageDescription
from bento.distutils.commands.sdist \
    import \
        sdist

from setup_common \
    import \
        generate_version_py

def create_ply_tabfile():
    from bento.core.parser.parser import parse
    parse('')

class install(old_install):
    def initialize_options(self):
        old_install.initialize_options(self)
        self.__files = []

    def _copy(self, source, target):
        if not os.path.exists(dirname(target)):
            os.makedirs(dirname(target))
        shutil.copy(source, target)
        self.__files.append(target)

    def run(self):
        create_ply_tabfile()

        self._copy(join("bento", "parsetab"),
                   join(self.install_purelib, "bento", "parsetab"))

        tdir = join(self.install_platlib, "bento", "commands", "wininst")
        for source in glob(join("bento", "commands", "wininst", "*.exe")):
            target = join(tdir, basename(source))
            self._copy(source, target)

        source = join("bento", "commands", "cli.exe")
        target = join(self.install_platlib, "bento", "commands", "cli.exe")
        self._copy(source, target)

        # MUST be run after __files contains everything
        old_install.run(self)

    def get_outputs(self):
        outfiles = old_install.get_outputs(self)
        outfiles.extend(self.__files)
        return outfiles

pkg = PackageDescription.from_file("bento.info")

DESCR = pkg.description
CLASSIFIERS = pkg.classifiers

METADATA = {
    'name': pkg.name,
    'version': pkg.version,
    'description': pkg.summary,
    'url': pkg.url,
    'author': pkg.author,
    'author_email': pkg.author_email,
    'license': pkg.license,
    'long_description': DESCR,
    'platforms': 'any',
    'classifiers': CLASSIFIERS,
}

PACKAGE_DATA = {
    'packages': pkg.packages,
    'entry_points': {
        'console_scripts': ['bentomaker=bentomakerlib.bentomaker:noexc_main']
    },
    'cmdclass': {"install": install, 'sdist': sdist}
}

if __name__ == '__main__':
    generate_version_py("bento/__dev_version.py")
    config = {}
    for d in (METADATA, PACKAGE_DATA):
        for k, v in d.items():
            config[k] = v
    setup(**config)
