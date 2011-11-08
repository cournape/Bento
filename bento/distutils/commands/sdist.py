import sys

from distutils.command.sdist \
    import \
        sdist as old_sdist

from bento.commands.wrapper_utils \
    import \
        run_cmd_in_context
from bento.commands.sdist \
    import \
        SdistCommand
from bento.commands.context \
    import \
        CmdContext

class sdist(old_sdist):
    def __init__(self, *a, **kw):
        old_sdist.__init__(self, *a, **kw)

    def initialize_options(self):
        old_sdist.initialize_options(self)

    def finalize_options(self):
        old_sdist.finalize_options(self)

    def run(self):
        dist = self.distribution

        cmd_name = "sdist"
        cmd_argv = ["--output-dir=%s" % self.dist_dir]
        cmd_context_klass = dist.global_context.get_context(cmd_name)
        cmd_klass = dist.global_context.get_command(cmd_name)
        run_cmd_in_context(cmd_klass, cmd_name, cmd_argv, cmd_context_klass,
                           dist.run_node, dist.top_node, dist.pkg)
