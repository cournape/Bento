import os
import sys
import shutil

from bento.compat.api \
    import \
        check_call, CalledProcessError

from bento.commands.errors \
    import \
        CommandExecutionFailure
from bento.commands.core \
    import \
        Command, get_command, get_command_names
from bento.core.utils \
    import \
        pprint, ensure_directory
from bento.core.package \
    import \
        PackageDescription
from bento._config \
    import \
        TOYDIST_SCRIPT, DISTCHECK_DIR

class DistCheckCommand(Command):
    long_descr = """\
Purpose: configure, build and test the project from sdist output
Usage:   bentomaker distcheck [OPTIONS]."""
    short_descr = "check that sdist output is buildable."
    def run(self, ctx):
        pprint('BLUE', "Distcheck...")
        bentomaker_script = os.path.abspath(sys.argv[0])

        pprint('PINK', "\t-> Running sdist...")
        sdist = get_command("sdist")()
        sdist.run(ctx)
        tarname = sdist.tarname
        tardir = sdist.topdir

        saved = os.getcwd()
        if os.path.exists(DISTCHECK_DIR):
            shutil.rmtree(DISTCHECK_DIR)
        os.makedirs(DISTCHECK_DIR)
        target = os.path.join(DISTCHECK_DIR,
                              os.path.basename(tarname))
        os.rename(tarname, target)
        tarname = os.path.basename(target)

        os.chdir(DISTCHECK_DIR)
        try:
            pprint('PINK', "\t-> Extracting sdist...")
            check_call(["tar", "-xzf", tarname])
            os.chdir(tardir)

            pprint('PINK', "\t-> Configuring from sdist...")
            check_call([bentomaker_script, "configure", "--prefix=tmp"])

            pprint('PINK', "\t-> Building from sdist...")
            check_call([bentomaker_script, "build"])

            pprint('PINK', "\t-> Building egg from sdist...")
            check_call([bentomaker_script, "build_egg"])

            if "test" in get_command_names():
                pprint('PINK', "\t-> Testing from sdist...")
                try:
                    check_call([bentomaker_script, "test"])
                except CalledProcessError, e:
                    raise CommandExecutionFailure(
                            "test command failed")
            else:
                pprint('YELLOW', "\t-> No test command defined, no testing")
        finally:
            os.chdir(saved)
