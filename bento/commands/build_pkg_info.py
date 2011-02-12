import optparse

from bento.core.package import \
        PackageDescription
from bento.conv import \
        write_pkg_info

from bento.commands.errors \
    import \
        UsageException
from bento.commands.core import \
        Command, SCRIPT_NAME

class BuildPkgInfoCommand(Command):
    long_descr = """\
Purpose: generate PKG-INFO file
Usage:   bentomaker build_pkg_info [OPTIONS]"""
    short_descr = "generate PKG-INFO file."
    common_options = Command.common_options + [
        optparse.Option("-o", "--output", dest="output", help="Output file for PKG-INFO"),
    ]

    def run(self, ctx):
        argv = ctx.get_command_arguments()
        p = ctx.options_context.parser
        o, a = p.parse_args(argv)
        if o.help:
            p.print_help()
            return
        if len(a) < 1:
            raise UsageException("%s: error: %s subcommand require an argument" \
                    % (SCRIPT_NAME, "parse"))
        else:
            filename = a[0]

        if not o.output:
            pkg_info = "PKG-INFO"
        else:
            pkg_info = o.output

        pkg = PackageDescription.from_file(filename)

        fid = open(pkg_info, "w")
        try:
            write_pkg_info(pkg, fid)
        finally:
            fid.close()
