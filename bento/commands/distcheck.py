import os
import sys
import shutil
import tarfile

from bento.compat.api \
    import \
        check_call, CalledProcessError, rename

from bento.commands.errors \
    import \
        CommandExecutionFailure
from bento.commands.core \
    import \
        Command, get_command, get_command_names
from bento.core.utils \
    import \
        pprint
from bento.core.package \
    import \
        PackageDescription
from bento._config \
    import \
        BENTO_SCRIPT, DISTCHECK_DIR

class DistCheckCommand(Command):
    long_descr = """\
Purpose: configure, build and test the project from sdist output
Usage:   bentomaker distcheck [OPTIONS]."""
    short_descr = "check that sdist output is buildable."
    def run(self, ctx):
        pprint('BLUE', "Distcheck...")
        bentomaker_script = os.path.abspath(sys.argv[0])
        if sys.platform == "win32":
            bentomaker_script = [sys.executable, bentomaker_script]
        else:
            bentomaker_script = [bentomaker_script]

        pprint('PINK', "\t-> Running sdist...")
        sdist = get_command("sdist")()
        sdist.setup_options_parser(None)
        sdist.run(ctx)
        tarname = sdist.tarname
        tardir = sdist.topdir

        saved = os.getcwd()
        if os.path.exists(DISTCHECK_DIR):
            shutil.rmtree(DISTCHECK_DIR)
        os.makedirs(DISTCHECK_DIR)
        target = os.path.join(DISTCHECK_DIR,
                              os.path.basename(tarname))
        rename(tarname, target)
        tarname = os.path.basename(target)

        os.chdir(DISTCHECK_DIR)
        try:
            pprint('PINK', "\t-> Extracting sdist...")
            tarball = tarfile.TarFile.gzopen(tarname)
            tarball.extractall()
            os.chdir(tardir)

            pprint('PINK', "\t-> Configuring from sdist...")
            check_call(bentomaker_script + ["configure", "--prefix=%s" % os.path.abspath("tmp")])

            pprint('PINK', "\t-> Building from sdist...")
            check_call(bentomaker_script + ["build", "-i"])

            pprint('PINK', "\t-> Building egg from sdist...")
            check_call(bentomaker_script + ["build_egg"])

            if sys.platform == "win32":
                pprint('PINK', "\t-> Building wininst from sdist...")
                check_call(bentomaker_script + ["build_wininst"])

            if "test" in get_command_names():
                pprint('PINK', "\t-> Testing from sdist...")
                try:
                    check_call(bentomaker_script + ["test"])
                except CalledProcessError, e:
                    raise CommandExecutionFailure(
                            "test command failed")
            else:
                pprint('YELLOW', "\t-> No test command defined, no testing")
        finally:
            os.chdir(saved)
