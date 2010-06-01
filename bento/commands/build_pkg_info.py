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
    opts = Command.opts + [
        {"opts": ["-o", "--output"], "dest": "output", "help": "Output file for PKG-INFO"},
    ]

    def run(self, ctx):
        self.set_option_parser()
        o, a = self.parser.parse_args(ctx.cmd_opts)
        if o.help:
            self.parser.print_help()
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
