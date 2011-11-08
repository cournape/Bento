import sys

from distutils.command.build \
    import \
        build as old_build

from bento.commands.wrapper_utils \
    import \
        run_cmd_in_context
from bento.commands.build \
    import \
        BuildCommand
from bento.commands.context \
    import \
        BuildYakuContext

class build(old_build):
    cmd_name = "build"
    def __init__(self, *a, **kw):
        old_build.__init__(self, *a, **kw)

    def initialize_options(self):
        old_build.initialize_options(self)

    def finalize_options(self):
        old_build.finalize_options(self)

    def run(self):
        self.run_command("config")

        dist = self.distribution

        cmd_context_klass = dist.global_context.retrieve_context(self.cmd_name)
        run_cmd_in_context(BuildCommand, self.cmd_name, [], cmd_context_klass,
                           dist.run_node, dist.top_node, dist.pkg)
