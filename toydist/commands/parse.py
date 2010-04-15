import os

from pprint import \
        pprint

from toydist.commands.errors \
    import \
        UsageException
from toydist.commands.core import \
        Command, SCRIPT_NAME
from toydist.core.parser.api \
    import \
        parse_to_dict, ParseError

class ParseCommand(Command):
    long_descr = """\
Purpose: query the given package description file (debugging tool)
Usage:   toymaker parse [OPTIONS]"""
    short_descr = "parse the package description file."
    opts = Command.opts + [
        {"opts": ["-f", "--flags"], "action": "store_true", "help": "print flags variables"},
        {"opts": ["-p", "--path"], "action": "store_true", "help": "print paths variables"},
        {"opts": ["-m", "--meta-field"], "dest": "meta_field", "help": "print given meta field"}
    ]

    def run(self, opts):
        self.set_option_parser()
        o, a = self.parser.parse_args(opts)
        if o.help:
            self.parser.print_help()
            return

        if len(a) < 1:
            filename = "toysetup.info"
        else:
            filename = a[0]

        if not os.path.exists(filename):
            raise UsageException("%s: error: file %s does not exist" % SCRIPT_NAME)

        f = open(filename, "r")
        try:
            data = f.read()
            try:
                parsed = parse_to_dict(data)
            except ParseError, e:
                msg = "Error while parsing file %s\n" % filename
                e.args = (msg,) +  e.args
                raise e
            if o.flags:
                try:
                    flags = parsed["flags"]
                    for flag in flags:
                        print flags[flag]
                except KeyError:
                    pass
            elif o.path:
                try:
                    paths = parsed["paths"]
                    for path in paths:
                        print paths[path]
                except KeyError:
                    pass
            elif o.meta_field:
                try:
                    print parsed[o.meta_field]
                except KeyError, e:
                    raise ValueError("Field %s not found in metadata" % o.meta_field)
            else:
                pprint(parsed)
        finally:
            f.close()

