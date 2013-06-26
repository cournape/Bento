import os

import os.path as op

from bento.utils.utils \
    import \
        subst_vars
from bento.installed_package_description \
    import \
        BuildManifest, build_manifest_meta_from_pkg
from bento._config \
    import \
        BUILD_MANIFEST_PATH

from bento.commands.core \
    import \
        Option
from bento.commands.core \
    import \
        Command
from bento.utils \
    import \
        cpu_count

class SectionWriter(object):
    def __init__(self):
        self.sections = {}

    def store(self, filename, pkg):
        meta = build_manifest_meta_from_pkg(pkg)
        p = BuildManifest(self.sections, meta, pkg.executables)
        if not op.exists(op.dirname(filename)):
            os.makedirs(op.dirname(filename))
        p.write(filename)


def jobs_callback(option, opt, value, parser):
    setattr(parser.values, option.dest, cpu_count())

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
                                  dest="jobs", action="callback", callback=jobs_callback),
                           Option("-v", "--verbose",
                                  help="Verbose output (yaku build only)",
                                  action="store_true")]

    def run(self, ctx):
        p = ctx.options_context.parser
        o, a = p.parse_args(ctx.command_argv)
        if o.help:
            p.print_help()
            return

        ctx.compile()
        ctx.post_compile()

    def finish(self, ctx):
        super(BuildCommand, self).finish(ctx)
        n = ctx.build_node.make_node(BUILD_MANIFEST_PATH)
        ctx.section_writer.store(n.abspath(), ctx.pkg)

def _config_content(paths):
    keys = sorted(paths.keys())
    n = max([len(k) for k in keys]) + 2
    content = []
    for name, value in sorted(paths.items()):
        content.append('%s = %r' % (name.upper().ljust(n), subst_vars(value, paths)))
    return "\n".join(content)

