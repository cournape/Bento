import os
import sys

from bento.core.utils \
    import \
        find_package, subst_vars, rename, ensure_dir
from bento.installed_package_description \
    import \
        InstalledPkgDescription, InstalledSection, ipkg_meta_from_pkg
from bento._config \
    import \
        IPKG_PATH
from bento.core.subpackage \
    import \
        get_extensions, get_compiled_libraries, get_packages
from bento.core.pkg_objects \
    import \
        DataFiles

from bento.commands.core \
    import \
        Option
from bento.commands \
    import \
        build_distutils
from bento.commands \
    import \
        build_yaku
from bento.commands.core \
    import \
        Command
from bento.commands.script_utils \
    import \
        create_posix_script, create_win32_script

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
        content.append('%s = "%s"' % (name.upper().ljust(n), subst_vars(value, paths)))
    return "\n".join(content)

