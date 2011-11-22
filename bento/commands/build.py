from bento.core.utils \
    import \
        subst_vars
from bento.installed_package_description \
    import \
        InstalledPkgDescription, ipkg_meta_from_pkg
from bento._config \
    import \
        IPKG_PATH

from bento.commands.core \
    import \
        Option
from bento.commands.core \
    import \
        Command

class SectionWriter(object):
    def __init__(self):
        self.sections = {}

    def store(self, filename, pkg):
        meta = ipkg_meta_from_pkg(pkg)
        p = InstalledPkgDescription(self.sections, meta, pkg.executables)
        p.write(filename)

class BuildCommand(Command):
    long_descr = """\
Purpose: build the project
Usage:   bentomaker build [OPTIONS]."""
    short_descr = "build the project."
    common_options = Command.common_options \
                        + [Option("-i", "--inplace",
                                  help="Build extensions in place", action="store_true"),
                           Option("-j", "--jobs",
                                  help="Parallel builds (yaku build only - EXPERIMENTAL)",
                                  dest="jobs"),
                           Option("-v", "--verbose",
                                  help="Verbose output (yaku build only)",
                                  action="store_true")]

    def __init__(self, *a, **kw):
        Command.__init__(self, *a, **kw)

    def run(self, ctx):
        argv = ctx.get_command_arguments()
        p = ctx.options_context.parser
        o, a = p.parse_args(argv)
        if o.help:
            p.print_help()
            return

        ctx.compile()
        ctx.post_compile()

    def shutdown(self, ctx):
        n = ctx.build_node.make_node(IPKG_PATH)
        ctx.section_writer.store(n.abspath(), ctx.pkg)

def _config_content(paths):
    keys = sorted(paths.keys())
    n = max([len(k) for k in keys]) + 2
    content = []
    for name, value in sorted(paths.items()):
        content.append('%s = %r' % (name.upper().ljust(n), subst_vars(value, paths)))
    return "\n".join(content)

