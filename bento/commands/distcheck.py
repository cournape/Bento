import os
import sys
import shutil
import tarfile
import subprocess

import os.path as op

from bento.compat.api \
    import \
        rename, CalledProcessError, TarFile

from bento.commands.errors \
    import \
        CommandExecutionFailure
from bento.commands.wrapper_utils \
    import \
        run_cmd_in_context
from bento.commands.core \
    import \
        Command, COMMANDS_REGISTRY
from bento.commands.context \
    import \
        CONTEXT_REGISTRY
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

def run_sdist(context):
    sdist_name = "sdist"
    sdist_klass = COMMANDS_REGISTRY.get_command(sdist_name)
    cmd_argv = []
    sdist_context_klass = CONTEXT_REGISTRY.get(sdist_name)
    sdist, sdist_context = run_cmd_in_context(sdist_klass,
                        sdist_name, cmd_argv, sdist_context_klass,
                        context.run_node, context.top_node, context.pkg)
    return sdist

class DistCheckCommand(Command):
    long_descr = """\
Purpose: configure, build and test the project from sdist output
Usage:   bentomaker distcheck [OPTIONS]."""
    short_descr = "check that sdist output is buildable."
    def run(self, ctx):
        pprint('BLUE', "Distcheck...")
        pprint('PINK', "\t-> Running sdist...")

        sdist = run_sdist(ctx)
        archive_root, archive_node = sdist.archive_root, sdist.archive_node

        saved = os.getcwd()

        distcheck_dir = ctx.build_node.make_node(DISTCHECK_DIR)
        if os.path.exists(distcheck_dir.abspath()):
            shutil.rmtree(distcheck_dir.abspath())
        distcheck_dir.mkdir()
        target = distcheck_dir.make_node(archive_node.name)
        rename(archive_node.abspath(), target.abspath())
        archive_node = os.path.basename(target.abspath())

        os.chdir(distcheck_dir.abspath())
        try:
            pprint('PINK', "\t-> Extracting sdist...")
            tarball = TarFile.gzopen(archive_node)
            tarball.extractall()
            os.chdir(archive_root)

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

            if sys.version_info[0] < 3:
                bentomaker_script = _BENTOMAKER_SCRIPT
            else:
                bentomaker_script = [sys.executable, "-m", "bentomakerlib.bentomaker"]

            pprint('PINK', "\t-> Configuring from sdist...")
            _call(bentomaker_script + ["configure", "--prefix=%s" % os.path.abspath("tmp")])

            pprint('PINK', "\t-> Building from sdist...")
            _call(bentomaker_script + ["build", "-i"])

            pprint('PINK', "\t-> Building egg from sdist...")
            _call(bentomaker_script + ["build_egg"])

            if sys.platform == "win32":
                pprint('PINK', "\t-> Building wininst from sdist...")
                _call(bentomaker_script + ["build_wininst"])

            if "test" in COMMANDS_REGISTRY.get_command_names():
                pprint('PINK', "\t-> Testing from sdist...")
                try:
                    _call(bentomaker_script + ["test"])
                except CalledProcessError, e:
                    raise CommandExecutionFailure(
                            "test command failed")
            else:
                pprint('YELLOW', "\t-> No test command defined, no testing")
        finally:
            os.chdir(saved)
