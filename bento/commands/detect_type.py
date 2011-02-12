import optparse
import StringIO

from bento.core.utils import \
        pprint

from bento.commands.core import \
        Command
from bento.commands.convert_utils import \
        whole_test


class DetectTypeCommand(Command):
    long_descr = """\
Purpose: detect type of distutils extension used by given setup.py
Usage:   bentomaker detect_type [OPTIONS]."""
    short_descr = "detect extension type."
    common_options = Command.common_options + [
        optparse.Option("-i", "--input", help="TODO", default="setup.py", dest="setup_file"),
        optparse.Option("-v", "--verbose", help="verbose run", action="store_true")]

    def run(self, ctx):
        argv = ctx.get_command_arguments()
        p = ctx.options_context.parser
        o, a = p.parse_args(argv)
        if o.help:
            p.print_help()
            return

        log = StringIO.StringIO()
        pprint("PINK",
               "=================================================================")
        pprint("PINK",
               "Detecting used distutils extension(s) ... (This may take a while)")
        type = whole_test(o.setup_file, o.verbose, log)
        pprint("PINK", "Done !")
        pprint("PINK",
               "=================================================================")
        pprint("GREEN", "Detected type: %s" % type)
