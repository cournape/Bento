from toydist.commands.sdist import create_tarball
from toydist.commands.core import register_command, Command
from toydist.commands.configure import get_configured_state
from toydist.core.utils import pprint
from toymakerlib.hooks import override

class TestCommand(Command):
    def run(self, opts):
        pprint('BLUE', "Running test command....")

# Example to register new commands
# XXX: a natural way to do this would be to mark classes which would follow
# the command protocol, but python 2.x does not support class decorators
def startup():
    register_command("test", TestCommand)

# Example to override existing toydist command:
@override
def sdist(opts):
    pkg = get_configured_state().pkg
    pkg.extra_source_files.append("toysetup.py")

    create_tarball(pkg)
