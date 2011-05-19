from distutils.command.config \
    import \
        config as old_config

from bento.core.platforms \
    import \
        get_scheme
from bento.distutils.utils \
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
        install = self.get_finalized_command("install")

        ## FIXME: this should be centralized with other scheme-related stuff
        #scheme = get_scheme(sys.platform)[0]
        #scheme["pkgname"] = pkg.name
        #py_version = sys.version.split()[0]
        #scheme["py_version_short"] = py_version[:3]
        scheme = {}
        if hasattr(install, "install_dir"):
            scheme["sitedir"] = install.install_dir
        scheme["prefix"] = install.install_base

        return scheme

    def run(self):
        from bento.commands.configure import ConfigureCommand
        from bento.commands.context import ConfigureYakuContext

        dist = self.distribution

        scheme = self._get_install_scheme()
        argv = []
        for k, v in scheme.iteritems():
            argv.append("--%s=%s" % (k, v))

        run_cmd_in_context(ConfigureCommand, "configure", argv, ConfigureYakuContext,
                           dist.run_node, dist.top_node, dist.pkg)
        #from bento._config import BENTO_SCRIPT
        #from bento.commands.configure import ConfigureCommand
        #from bento.commands.options import OptionsContext
        #from bento.compat.api import relpath

        #from bento.commands.configure import _setup_options_parser

        #package_options = PackageOptions.from_file(BENTO_SCRIPT)

        #dist = self.distribution
        #top_node = dist.top_node

        #cmd = ConfigureCommand()
        #options_ctx = OptionsContext.from_command(cmd)
        #_setup_options_parser(options_ctx, package_options)

        #ctx = ConfigureYakuContext(argv, options_ctx, dist.pkg, dist.run_node)
        #ctx.package_options = package_options

        #cmd_funcs = [(cmd.run, dist.top_node.abspath())]

        #try:
        #    while cmd_funcs:
        #        cmd_func, local_dir = cmd_funcs.pop(0)
        #        local_node = top_node.find_dir(relpath(local_dir, top_node.abspath()))
        #        ctx.pre_recurse(local_node)
        #        try:
        #            cmd_func(ctx)
        #        finally:
        #            ctx.post_recurse()

        #    cmd.shutdown(ctx)
        #finally:
        #    ctx.shutdown()
