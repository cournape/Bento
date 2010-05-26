import os
import sys

from toydist.commands.core \
    import \
        register_command, Command, get_command
from toydist.core.utils \
    import \
        pprint, ensure_directory

class TestCommand(Command):
    def run(self, opts):
        pprint('BLUE', "Running test command....")
        saved = os.getcwd()

        os.chdir("tests")
        try:
            from nose.core import main
            # XXX: find out why nose.core.main screws up traceback,
            # and exits python interpreter here
            main(argv=sys.argv[:1])
        finally:
            os.chdir(saved)

def startup():
    from toydist.commands.distcheck import DistCheckCommand
    #register_command("test", TestCommand)
    register_command("distcheck", DistCheckCommand)
