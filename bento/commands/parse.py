import os

from pprint import \
        pprint

from bento.commands.errors \
    import \
        UsageException
from bento.commands.core import \
        Command, Option
from bento.core.parser.api \
    import \
        build_ast_from_data, ParseError
from bento.core.utils \
    import \
        extract_exception

class ParseCommand(Command):
    long_descr = """\
Purpose: query the given package description file (debugging tool)
Usage:   bentomaker parse [OPTIONS]"""
    short_descr = "parse the package description file."
    common_options = Command.common_options + [
        Option("-f", "--flags", action="store_true",
               help="print flags variables"),
        Option("-p", "--path", action="store_true",
               help="print paths variables"),
        Option("-m", "--meta-field", dest="meta_field",
               help="print given meta field")]

    def run(self, ctx):
        argv = ctx.get_command_arguments()
        p = ctx.options_context.parser
        o, a = p.parse_args(argv)
        if o.help:
            p.print_help()
            return

        if len(a) < 1:
            filename = "bento.info"
        else:
            filename = a[0]

        if not os.path.exists(filename):
            raise UsageException("%s: error: file %s does not exist" % "bentomaker")

        f = open(filename, "r")
        try:
            data = f.read()
            try:
                parsed = build_ast_from_data(data)
            except ParseError:
                e = extract_exception()
                msg = "Error while parsing file %s\n" % filename
                e.args = (msg,) +  e.args
                raise e
            if o.flags:
                try:
                    flags = parsed["flags"]
                    for flag in flags:
                        print(flags[flag])
                except KeyError:
                    pass
            elif o.path:
                try:
                    paths = parsed["paths"]
                    for path in paths:
                        print(paths[path])
                except KeyError:
                    pass
            elif o.meta_field:
                try:
                    print(parsed[o.meta_field])
                except KeyError:
                    raise ValueError("Field %s not found in metadata" % o.meta_field)
            else:
                pprint(parsed)
        finally:
            f.close()

