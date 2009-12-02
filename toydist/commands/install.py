import os
import shutil

from toydist.installed_package_description import \
    InstalledPkgDescription, read_installed_pkg_description

from toydist.commands.core import \
    Command

def install_sections(sections, installer=None):
    if not installer:
        installer = shutil.copy

    for section in sections:
        for source, target in sections[section]:
            if not os.path.exists(os.path.dirname(target)):
                os.makedirs(os.path.dirname(target))
            installer(source, target)

def installer(source, target):
    cmd = ["install", "-m", "644", source, target]
    strcmd = "INSTALL %s -> %s" % (source, target)
    pprint('GREEN', strcmd)
    subprocess.check_call(cmd)

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

        sections = read_installed_pkg_description("installed-pkg-info")

        #install_sections(sections, installer=installer)
        install_sections(sections, installer=shutil.copy)

