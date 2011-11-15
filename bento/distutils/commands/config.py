import os
import sys

import os.path as op

from distutils.command.config \
    import \
        config as old_config

from bento.core.platforms \
    import \
        get_scheme

class config(old_config):
    cmd_name = "configure"
    def __init__(self, *a, **kw):
        old_config.__init__(self, *a, **kw)

    def initialize_options(self):
        old_config.initialize_options(self)

    def finalize_options(self):
        old_config.finalize_options(self)

    def _get_install_scheme(self):
        pkg = self.distribution.pkg

        install = self.get_finalized_command("install")
        return install.scheme

    def run(self):
        from bento.commands.configure import ConfigureCommand
        from bento.commands.context import ConfigureYakuContext

        dist = self.distribution

        scheme = self._get_install_scheme()
        argv = []
        for k, v in scheme.items():
            if k == "exec_prefix":
                k = "exec-prefix"
            argv.append("--%s=%s" % (k, v))

        dist.run_command_in_context(self.cmd_name, argv)
