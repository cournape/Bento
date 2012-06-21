import sys

from distutils.command.sdist \
    import \
        sdist as old_sdist

class sdist(old_sdist):
    def run(self):
        cmd_name = "sdist"
        cmd_argv = ["--output-dir=%s" % self.dist_dir]
        self.distribution.run_command_in_context(cmd_name, cmd_argv)
