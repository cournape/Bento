import os
import shutil
import subprocess

from bento.installed_package_description import \
    InstalledPkgDescription, iter_files

from bento.commands.errors \
    import \
        UsageException
from bento.commands.core import \
    Command
from bento.core.utils import \
    pprint

def copy_installer(source, target, kind):
    dtarget = os.path.dirname(target)
    if not os.path.exists(dtarget):
        os.makedirs(dtarget)
    shutil.copy(source, target)
    if kind == "executables":
        os.chmod(target, 0755)

def unix_installer(source, target, kind):
    if kind in ["executables"]:
        mode = "755"
    else:
        mode = "644"
    cmd = ["install", "-m", mode, source, target]
    strcmd = "INSTALL %s -> %s" % (source, target)
    pprint('GREEN', strcmd)
    if not os.path.exists(os.path.dirname(target)):
        os.makedirs(os.path.dirname(target))
    subprocess.check_call(cmd)

class InstallCommand(Command):
    long_descr = """\
Purpose: install the project
Usage:   bentomaker install [OPTIONS]."""
    short_descr = "install the project."
    def run(self, ctx):
        opts = ctx.cmd_opts
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

        for kind, source, target in iter_files(file_sections):
            copy_installer(source, target, kind)
