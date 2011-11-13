import sys

from distutils.command.sdist \
    import \
        sdist as old_sdist

class sdist(old_sdist):
    def __init__(self, *a, **kw):
        old_sdist.__init__(self, *a, **kw)

    def initialize_options(self):
        old_sdist.initialize_options(self)

    def finalize_options(self):
        old_sdist.finalize_options(self)

    def run(self):
        cmd_name = "sdist"
        cmd_argv = ["--output-dir=%s" % self.dist_dir]
        self.distribution.run_command_in_context(cmd_name, cmd_argv)
