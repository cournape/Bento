import os
import sys
import shutil
import subprocess

from toydist.commands.core \
    import \
        register_command, Command, get_command
from toydist.core.utils \
    import \
        pprint

def ensure_directory(d):
    if not os.path.exists(d):
        os.makedirs(d)

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

class DistCheckCommand(Command):
    def run(self, opts):
        pprint('BLUE', "Distcheck...")

        pprint('PINK', "\t-> Running sdist...")
        sdist = get_command("sdist")
        sdist().run([])

        tarname = "toydist-0.0.2.tar.gz"

        saved = os.getcwd()
        if os.path.exists(".distcheck"):
            shutil.rmtree(".distcheck")
        ensure_directory(".distcheck")
        os.rename(tarname, os.path.join(".distcheck", tarname))

        os.chdir(".distcheck")
        try:
            pprint('PINK', "\t-> Extracting sdist...")
            subprocess.check_call(["tar", "-xzf", tarname])
            os.chdir("toydist-0.0.2")

            pprint('PINK', "\t-> Configuring from sdist...")
            subprocess.check_call(["../../toymaker", "configure", "--prefix=tmp"])

            pprint('PINK', "\t-> Building from sdist...")
            subprocess.check_call(["../../toymaker", "build"])

            pprint('PINK', "\t-> Building egg from sdist...")
            subprocess.check_call(["../../toymaker", "build_egg"])

            pprint('PINK', "\t-> Testing from sdist...")
            subprocess.check_call(["../../toymaker", "test"])
        finally:
            os.chdir(saved)

def startup():
    register_command("test", TestCommand)
    register_command("distcheck", DistCheckCommand)
