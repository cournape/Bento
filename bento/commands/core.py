import getopt
import copy

from optparse \
    import \
        Option, OptionGroup

import bento

from bento.commands.options \
    import \
        OptionParser

from bento.commands._config \
    import \
        SCRIPT_NAME
from bento.commands.errors \
    import \
        UsageException, OptionError

USAGE = """\
Toymaker %(version)s -- an alternative to distutils-based systems
Usage: %(name)s [command [options]]
"""

# FIXME: better way to register commands
_CMDS_TO_CLASS = {}
_PCMDS_TO_CLASS = {}
_UCMDS_TO_CLASS = {}

def get_command_names():
    return _CMDS_TO_CLASS.keys()

def get_public_command_names():
    return _UCMDS_TO_CLASS.keys()

def get_command(name):
    return _CMDS_TO_CLASS[name]

def register_command(name, klass, public=True):
    global _CMDS_TO_CLASS
    global _UCMDS_TO_CLASS
    global _PCMDS_TO_CLASS

    if public:
        _UCMDS_TO_CLASS[name] = klass
    else:
        _PCMDS_TO_CLASS[name] = klass

    _CMDS_TO_CLASS = dict([(k, v) for k, v in _PCMDS_TO_CLASS.items()])
    _CMDS_TO_CLASS.update(_UCMDS_TO_CLASS)

class Command(object):
    long_descr = None
    short_descr = None
    # XXX: decide how to deal with subcommands options
    opts = [Option('-h', '--help',
                   help="Show this message and exits.",
                   action="store_true")]

    def __init__(self):
        self.parser = None

    def _create_parser(self):
        if self.parser is None:
            self.parser = OptionParser(self.long_descr.splitlines()[1])

    def reset_parser(self):
        self.parser = None
        self._create_parser()

    def set_option_parser(self):
        self._create_parser()
        try:
            oo = copy.deepcopy(self.opts)
            for o in oo:
                self.parser.add_option(o)
        except getopt.GetoptError, e:
            raise UsageException("%s: error: %s for help subcommand" % (SCRIPT_NAME, e))

    def run(self, opts):
        raise NotImplementedError("run method should be implemented by command classes.")

class HelpCommand(Command):
    long_descr = """\
Purpose: Show help on a command or other topic.
Usage:   bentomaker help [TOPIC] or bentomaker help [COMMAND]."""
    short_descr = "gives help on a given topic or command."
    def run(self, cmd_args):
        if len(cmd_args) < 1:
            print get_simple_usage()
            return

        # Parse the options for help command itself
        cmd_name = None
        help_args = []
        if not cmd_args[0].startswith('-'):
            cmd_name = cmd_args[0]
            cmd_args.pop(0)
        else:
            # eat all the help options
            _args = [cmd_args.pop(0)]
            while not _args[0].startswith('-') and len(cmd_args) > 0:
                _args.append(cmd_args.pop(0))
            help_args = _args
            cmd_name = cmd_args[0]

        # XXX: overkill as we don't support any options for now
        try:
            parser = OptionParser()
            for o in self.opts:
                parser.add_option(o)
            parser.parse_args(help_args)
        except OptionError, e:
            raise UsageException("%s: error: %s for help subcommand" % (SCRIPT_NAME, e))

        if cmd_name == "commands":
            print get_usage()
            return

        if not cmd_name in get_command_names():
            raise UsageException("%s: error: %s not recognized" % (SCRIPT_NAME, cmd_name))
        cmd_class = get_command(cmd_name)

        parser = OptionParser(usage='')
        for o in cmd_class.opts:
            parser.add_option(o)
        print cmd_class.long_descr
        print ""
        parser.print_help()

def fill_string(s, minlen):
    if len(s) < minlen:
        s += " " * (minlen - len(s))
    return s

def get_simple_usage():
    ret = [USAGE % {"name": SCRIPT_NAME,
                    "version": bento.__version__}]
    ret.append("Basic Commands:")

    commands = []

    def add_group(cmd_names):
        for name in cmd_names:
            v = get_command(name)
            doc = v.short_descr
            if doc is None:
                doc = "undocumented"
            header = "  %(script)s %(cmd_name)s" % \
                        {"script": SCRIPT_NAME,
                         "cmd_name": name}
            commands.append((header, doc))
    add_group(["configure", "build", "install"])
    commands.append(("", ""))
    add_group(["sdist", "build_wininst", "build_egg"])
    commands.append(("", ""))

    commands.append(("  %s help configure" % SCRIPT_NAME,
                     "more help on e.g. configure command"))
    commands.append(("  %s help commands" % SCRIPT_NAME,
                     "list all commands"))

    minlen = max([len(header) for header, hlp in commands]) + 2
    for header, hlp in commands:
        ret.append(fill_string(header, minlen) + hlp)
    return "\n".join(ret)

def get_usage():
    ret = [USAGE % {"name": SCRIPT_NAME,
                    "version": bento.__version__}]
    ret.append("Toydist commands:")

    commands = []
    cmd_names = sorted(get_public_command_names())
    for name in cmd_names:
        v = get_command(name)
        doc = v.short_descr
        if doc is None:
            doc = "undocumented"
        header = "  %s" % name
        commands.append((header, doc))

    minlen = max([len(header) for header, hlp in commands]) + 2
    for header, hlp in commands:
        ret.append(fill_string(header, minlen) + hlp)
    return "\n".join(ret)
