import os
import shutil

from toydist.installed_package_description import \
    InstalledPkgDescription, iter_files

from toydist.commands.core import \
    Command, UsageException

def install_sections(sections, installer=None):
    if not installer:
        installer = copy_installer

    for kind, source, target in iter_files(sections):
        installer(source, target, kind)

def copy_installer(source, target, kind):
    dtarget = os.path.dirname(target)
    if not os.path.exists(dtarget):
        os.makedirs(dtarget)
    shutil.copy(source, target)
    if kind == "executables":
        os.chmod(target, 0555)

class InstallCommand(Command):
    long_descr = """\
Purpose: install the project
Usage:   toymaker install [OPTIONS]."""
    short_descr = "install the project."
    def run(self, opts):
        self.set_option_parser()
        o, a = self.parser.parse_args(opts)
        if o.help:
            self.parser.print_help()
            return

        if not os.path.exists("installed-pkg-info"):
            msg = "No installed-pkg-info file found ! (Did you run build ?)"
            raise UsageException(msg)

        ipkg = InstalledPkgDescription.from_file("installed-pkg-info")
        file_sections = ipkg.resolve_paths()

        install_sections(file_sections, installer=copy_installer)
