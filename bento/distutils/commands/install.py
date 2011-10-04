from bento.distutils.utils \
    import \
        _is_setuptools_activated
if _is_setuptools_activated():
    from setuptools.command.install \
        import \
            install as old_install
else:
    from distutils.command.install \
        import \
            install as old_install

from bento._config \
    import \
        IPKG_PATH
from bento.installed_package_description \
    import \
        InstalledPkgDescription, iter_files
from bento.compat.api \
    import \
        relpath

from bento.commands.install \
    import \
        InstallCommand
from bento.commands.context \
    import \
        CmdContext
from bento.commands.options \
    import \
        OptionsContext
from bento.commands.wrapper_utils \
    import \
        run_cmd_in_context

class install(old_install):
    def initialize_options(self):
        old_install.initialize_options(self)

    def finalize_options(self):
        old_install.finalize_options(self)

    def run(self):
        self.run_command("build")
        dist = self.distribution
        args = []

        if self.dry_run == 1:
            args.append("--dry-run")
        run_cmd_in_context(InstallCommand, "install", args, CmdContext,
                           dist.run_node, dist.top_node, dist.pkg)
        if self.record:
            self.write_record()

    def write_record(self):
        dist = self.distribution

        install = InstallCommand()
        options_context = OptionsContext.from_command(install)
        context = CmdContext([], options_context, dist.pkg, dist.run_node)
        if self.record:
            n = context.build_node.make_node(IPKG_PATH)
            ipkg = InstalledPkgDescription.from_file(n.abspath())
            scheme = context.get_paths_scheme()
            ipkg.update_paths(scheme)
            file_sections = ipkg.resolve_paths(src_root_node=context.build_node)

            fid = open(self.record, "w")
            try:
                for kind, source, target in iter_files(file_sections):
                    fid.write("%s\n" % target.abspath())
            finally:
                fid.close()
