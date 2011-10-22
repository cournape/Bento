import getopt
import copy

from optparse \
    import \
        Option, OptionGroup, OptionParser

import bento

from bento._config \
    import \
        BENTO_SCRIPT
from bento.core.utils \
    import \
        to_camel_case
from bento.commands.options \
    import \
        OptionsContext

from bento.commands.errors \
    import \
        UsageException

USAGE = """\
bentomaker %(version)s -- an alternative to distutils-based systems
Usage: %(name)s [command [options]]
"""

class Command(object):
    long_descr = """\
Purpose: command's purposed (default description)
Usage: command's usage (default description)
"""
    short_descr = None
    # XXX: decide how to deal with subcommands options
    common_options = [Option('-h', '--help',
                             help="Show this message and exits.",
                             action="store_true")]

    def run(self, ctx):
        raise NotImplementedError("run method should be implemented by command classes.")

    def shutdown(self, ctx):
        pass

class HelpCommand(Command):
    long_descr = """\
Purpose: Show help on a command or other topic.
Usage:   bentomaker help [TOPIC] or bentomaker help [COMMAND]."""
    short_descr = "gives help on a given topic or command."
    def run(self, ctx):
        cmd_args = ctx.get_command_arguments()
        p = ctx.options_context.parser
        o, a = p.parse_args(cmd_args)
        if o.help:
            p.print_help()
            return
        if len(a) < 1:
            print(get_simple_usage())
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

        options_context = ctx.options_registry.get_options(cmd_name)
        if ctx.options_registry.is_registered(cmd_name):
            p = options_context.parser
            p.print_help()
        else:
            raise UsageException("error: command %s not recognized" % cmd_name)

def fill_string(s, minlen):
    if len(s) < minlen:
        s += " " * (minlen - len(s))
    return s

def get_simple_usage():
    ret = [USAGE % {"name": "bentomaker",
                    "version": bento.__version__}]
    ret.append("Basic Commands:")

    commands = []

    def add_group(cmd_names):
        for name in cmd_names:
            v = COMMANDS_REGISTRY.get_command(name)
            doc = v.short_descr
            if doc is None:
                doc = "undocumented"
            header = "  %(script)s %(cmd_name)s" % \
                        {"script": "bentomaker",
                         "cmd_name": name}
            commands.append((header, doc))
    add_group(["configure", "build", "install"])
    commands.append(("", ""))
    add_group(["sdist", "build_wininst", "build_egg"])
    commands.append(("", ""))

    commands.append(("  %s help configure" % "bentomaker",
                     "more help on e.g. configure command"))
    commands.append(("  %s help commands" % "bentomaker",
                     "list all commands"))
    commands.append(("  %s help globals" % "bentomaker",
                     "show global options"))

    minlen = max([len(header) for header, hlp in commands]) + 2
    for header, hlp in commands:
        ret.append(fill_string(header, minlen) + hlp)
    return "\n".join(ret)

# Decorator to create a new command class from a simple function
def command(f):
    bypass_help = True
    def _dec(f):
        klass_name = "%sCommand" % to_camel_case(f.__name__)

        class _CmdFakeMetaclass(type):
            def __init__(cls, name, bases, d):
                super(_CmdFakeMetaclass, cls).__init__(name, bases, d)
                name = cls.__name__

        klass = _CmdFakeMetaclass(klass_name, (Command,), {})

        if f.__name__.startswith("_"):
            COMMANDS_REGISTRY.register_command(f.__name__, klass, public=False)
        else:
            COMMANDS_REGISTRY.register_command(f.__name__, klass)
        if bypass_help:
            def run(self, ctx):
                o, a = ctx.options_context.parser.parse_args(ctx.get_command_arguments())
                if o.help:
                    ctx.options_context.parser.print_help()
                    return
                return f(ctx)
        else:
            run = lambda self, ctx: f(ctx)
        klass.run = run
        if f.__doc__:
            klass.long_descr = f.__doc__
        return f
    return _dec(f)

class CommandRegistry(object):
    def __init__(self):
        # command line name -> command class
        self._klasses = {}
        # command line name -> None for private commands
        self._privates = {}

    def register_command(self, name, cmd_klass, public=True):
        if name in self._klasses:
            raise ValueError("context for command %r already registered !" % name)
        else:
            self._klasses[name] = cmd_klass
            if not public:
                self._privates[name] = None

    def get_command(self, name):
        cmd_klass = self._klasses.get(name, None)
        if cmd_klass is None:
            raise ValueError("No command class registered for name %r" % name)
        else:
            return cmd_klass

    def get_command_names(self):
        return self._klasses.keys()

    def get_public_command_names(self):
        return [k for k in self._klasses.keys() if not k in self._privates]

    def get_command_name(self, klass):
        for k, v in self._klasses.iteritems():
            if v == klass:
                return k
        raise ValueError("Unregistered class %r" % klass)

    def get_command_name_from_class_name(self, class_name):
        for k, v in self._klasses.iteritems():
            if v.__name__ == class_name:
                return k
        raise ValueError("Unregistered class %r" % class_name)

# FIXME: singleton
COMMANDS_REGISTRY = CommandRegistry()
