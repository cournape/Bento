import os
import sys
import shutil
import subprocess

from toydist.core.package \
    import \
        PackageDescription
from toydist.commands.core \
    import \
        register_command, Command, get_command
from toydist.core.utils \
    import \
        pprint, ensure_directory
from toydist._config \
    import \
        TOYDIST_SCRIPT

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

        pkg = PackageDescription.from_file(TOYDIST_SCRIPT)
        tarname = "%s-%s.tar.gz" % (pkg.name, pkg.version)
        tardir = "%s-%s" % (pkg.name, pkg.version)

        saved = os.getcwd()
        if os.path.exists(".distcheck"):
            shutil.rmtree(".distcheck")
        os.makedirs(".distcheck")
        os.rename(tarname, os.path.join(".distcheck", tarname))

        os.chdir(".distcheck")
        try:
            pprint('PINK', "\t-> Extracting sdist...")
            subprocess.check_call(["tar", "-xzf", tarname])
            os.chdir(tardir)

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
