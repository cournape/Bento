from toydist.commands.sdist import create_tarball
from toydist.commands.core import register_command, Command
from toydist.core import PackageDescription
from toydist.core.utils import pprint
from toymakerlib.hooks import *

class TestCommand(Command):
    def run(self, opts):
        pprint('BLUE', "Running test command....")

# Example to register new commands
# XXX: the natural way to do this would be to mark classes which would follow
# the command protocol, but python 2.x does not support class decorators
def startup():
    register_command("test", TestCommand)

# Example to override existing toydist command
@override
def sdist(opts):
    pkg = PackageDescription.from_file("toysetup.info")
    pkg.extra_source_files = ["toysetup.py", "toysetup.info"]
    pkg.packages = []
    pkg.data_files = {}

    create_tarball(pkg, "fake_tarball.tgz")
