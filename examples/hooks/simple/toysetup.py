from bento.commands.sdist import create_tarball
from bento.commands.core import register_command, Command
from bento.commands.configure import get_configured_state
from bento.core.utils import pprint
from bento.commands.hooks import override

class TestCommand(Command):
    def run(self, opts):
        pprint('BLUE', "Running test command....")

# Example to register new commands: startup function is called everytime
# toymaker is run, and very early on. This is the place where to e.g. register
# new commands
def startup():
    register_command("test", TestCommand)

# Example to override existing toydist command: we add an extra source file
# here instead of adding it in bento.info. This may be used to e.g. support
# the setuptools feature of automatically adding files in VCS.
@override
def sdist(opts):
    ctx = get_configured_state()
    pkg = ctx.pkg
    pkg.extra_source_files.append("toysetup.py.bak")

    create_tarball(pkg)
