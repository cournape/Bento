import os
import sys
import shutil

from toydist.compat.api \
    import \
        check_call, CalledProcessError

from toydist.commands.errors \
    import \
        CommandExecutionFailure
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
        TOYDIST_SCRIPT, DISTCHECK_DIR

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
        if os.path.exists(DISTCHECK_DIR):
            shutil.rmtree(DISTCHECK_DIR)
        os.makedirs(DISTCHECK_DIR)
        os.rename(tarname, os.path.join(DISTCHECK_DIR, tarname))

        os.chdir(DISTCHECK_DIR)
        try:
            pprint('PINK', "\t-> Extracting sdist...")
            check_call(["tar", "-xzf", tarname])
            os.chdir(tardir)

            pprint('PINK', "\t-> Configuring from sdist...")
            check_call([toymaker_script, "configure", "--prefix=tmp"])

            pprint('PINK', "\t-> Building from sdist...")
            check_call([toymaker_script, "build"])

            pprint('PINK', "\t-> Building egg from sdist...")
            check_call([toymaker_script, "build_egg"])

            if "test" in get_command_names():
                pprint('PINK', "\t-> Testing from sdist...")
                try:
                    check_call([toymaker_script, "test"])
                except CalledProcessError, e:
                    raise CommandExecutionFailure(
                            "test command failed")
            else:
                pprint('YELLOW', "\t-> No test command defined, no testing")
        finally:
            os.chdir(saved)
