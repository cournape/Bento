import os
import sys

import os.path as op

from distutils.command.config \
    import \
        config as old_config

from bento.core.platforms \
    import \
        get_scheme
from bento.commands.wrapper_utils \
    import \
        run_cmd_in_context

class config(old_config):
    def __init__(self, *a, **kw):
        old_config.__init__(self, *a, **kw)

    def initialize_options(self):
        old_config.initialize_options(self)

    def finalize_options(self):
        old_config.finalize_options(self)

    def _get_install_scheme(self):
        pkg = self.distribution.pkg

        # XXX: we cannot use get_finalized_command("install"), because we need
        # to override scheme when --root is given, and this is done in the
        # __init__method of install.
        install = self.distribution.get_command_obj("install")
        install.change_roots = lambda *args: None
        self.reinitialize_command("install")
        install.ensure_finalized()

        scheme = {}

        # This mess is taken from distutils.install. This is awfully
        # complicated, but I see no way to install at the same location as unix
        # without recreating the whole distutils scheme logic madness.
        if os.name == "posix":
            if hasattr(install, "install_layout") and install.install_layout:
                raise ValueError("install layout option not supported !")
            elif (hasattr(install, "prefix_option") and install.prefix_option and os.path.normpath(install.prefix) != '/usr/local') \
                or 'PYTHONUSERBASE' in os.environ \
                or 'real_prefix' in sys.__dict__:
                    scheme["prefix"] = scheme["exec_prefix"] = install.install_base
                    scheme["sitedir"] = install.install_purelib
                    scheme["includedir"] = install.install_headers
            else:
                scheme["prefix"] = op.join(install.install_base, "local")
                scheme["exec-prefix"] = op.join(install.install_platbase, "local")
                scheme["sitedir"] = install.install_purelib
                scheme["includedir"] = install.install_headers

        if install.root:
            scheme["destdir"] = install.root
        for k, v in scheme.items():
            if not op.isabs(v):
                scheme[k] = op.join(os.getcwd(), v)

        return scheme

    def run(self):
        from bento.commands.configure import ConfigureCommand
        from bento.commands.context import ConfigureYakuContext

        dist = self.distribution

        scheme = self._get_install_scheme()
        argv = []
        for k, v in scheme.iteritems():
            if k == "exec_prefix":
                k = "exec-prefix"
            argv.append("--%s=%s" % (k, v))

        run_cmd_in_context(ConfigureCommand, "configure", argv, ConfigureYakuContext,
                           dist.run_node, dist.top_node, dist.pkg)
