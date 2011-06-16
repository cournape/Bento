import os
import sys
import shutil
import tarfile
import subprocess

import os.path as op

from bento.compat.api \
    import \
        rename, CalledProcessError

from bento.commands.errors \
    import \
        CommandExecutionFailure
from bento.commands.core \
    import \
        Command, COMMANDS_REGISTRY
from bento.core.utils \
    import \
        pprint
from bento.core.package \
    import \
        PackageDescription
from bento._config \
    import \
        BENTO_SCRIPT, DISTCHECK_DIR

import bentomakerlib

_BENTOMAKER_SCRIPT = [op.join(op.dirname(bentomakerlib.__file__), os.pardir, "bentomaker")]

class DistCheckCommand(Command):
    long_descr = """\
Purpose: configure, build and test the project from sdist output
Usage:   bentomaker distcheck [OPTIONS]."""
    short_descr = "check that sdist output is buildable."
    def run(self, ctx):
        pprint('BLUE', "Distcheck...")
        pprint('PINK', "\t-> Running sdist...")
        sdist = COMMANDS_REGISTRY.get_command("sdist")()
        sdist.run(ctx)
        tarname = sdist.tarname
        tardir = sdist.topdir

        saved = os.getcwd()

        distcheck_dir = ctx.build_node.make_node(DISTCHECK_DIR)
        if os.path.exists(distcheck_dir.abspath()):
            shutil.rmtree(distcheck_dir.abspath())
        distcheck_dir.mkdir()
        target = distcheck_dir.make_node(os.path.basename(tarname))
        rename(tarname, target.abspath())
        tarname = os.path.basename(target.abspath())

        os.chdir(distcheck_dir.abspath())
        try:
            pprint('PINK', "\t-> Extracting sdist...")
            tarball = tarfile.TarFile.gzopen(tarname)
            tarball.extractall()
            os.chdir(tardir)

            def _call(cmd):
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = p.communicate()
                stdout = stdout.strip()
                stderr = stderr.strip()
                if stdout:
                    print stdout.decode()
                if stderr:
                    print stderr.decode()
                if p.returncode != 0:
                    raise CalledProcessError(p.returncode, cmd)

            pprint('PINK', "\t-> Configuring from sdist...")
            _call(_BENTOMAKER_SCRIPT + ["configure", "--prefix=%s" % os.path.abspath("tmp")])

            pprint('PINK', "\t-> Building from sdist...")
            _call(_BENTOMAKER_SCRIPT + ["build", "-i"])

            pprint('PINK', "\t-> Building egg from sdist...")
            _call(_BENTOMAKER_SCRIPT + ["build_egg"])

            if sys.platform == "win32":
                pprint('PINK', "\t-> Building wininst from sdist...")
                _call(_BENTOMAKER_SCRIPT + ["build_wininst"])

            if "test" in COMMANDS_REGISTRY.get_command_names():
                pprint('PINK', "\t-> Testing from sdist...")
                try:
                    _call(_BENTOMAKER_SCRIPT + ["test"])
                except CalledProcessError, e:
                    raise CommandExecutionFailure(
                            "test command failed")
            else:
                pprint('YELLOW', "\t-> No test command defined, no testing")
        finally:
            os.chdir(saved)
