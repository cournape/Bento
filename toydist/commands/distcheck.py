import os
import sys
import shutil
import subprocess

from toydist.commands.core \
    import \
        Command, get_command, get_command_names
from toydist.core.utils \
    import \
        pprint, ensure_directory
from toydist.core.package \
    import \
        PackageDescription
from toydist._config \
    import \
        TOYDIST_SCRIPT

class DistCheckCommand(Command):
    def run(self, opts):
        pprint('BLUE', "Distcheck...")
        toymaker_script = os.path.abspath(sys.argv[0])

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
            subprocess.check_call([toymaker_script, "configure", "--prefix=tmp"])

            pprint('PINK', "\t-> Building from sdist...")
            subprocess.check_call([toymaker_script, "build"])

            pprint('PINK', "\t-> Building egg from sdist...")
            subprocess.check_call([toymaker_script, "build_egg"])

            if "test" in get_command_names():
                pprint('PINK', "\t-> Testing from sdist...")
                subprocess.check_call([toymaker_script, "test"])
            else:
                pprint('YELLOW', "\t-> No test command defined, no testing")
        finally:
            os.chdir(saved)
