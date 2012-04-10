from optparse \
    import \
        Option

import bento

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

    def init(self, ctx):
        pass

    def finish(self, ctx):
        pass

class WrappedCommand(Command):
    def __init__(self, func):
        super(WrappedCommand, self).__init__()
        self._func = func
        self.name = func.__name__

    def __call__(self, ctx):
        return self.run(ctx)

    def run(self, ctx):
        return self._func(ctx)

    def __getattr__(self, k):
        return getattr(self._func, k)

class HelpCommand(Command):
    long_descr = """\
Purpose: Show help on a command or other topic.
Usage:   bentomaker help [TOPIC] or bentomaker help [COMMAND]."""
    short_descr = "gives help on a given topic or command."
    def run(self, ctx):
        cmd_args = ctx.command_argv
        p = ctx.options_context.parser
        o, a = p.parse_args(cmd_args)
        if o.help:
            p.print_help()
            return
        if len(a) < 1:
            print(get_simple_usage(ctx))
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

        if ctx.is_options_context_registered(cmd_name):
            options_context = ctx.retrieve_options_context(cmd_name)
            p = options_context.parser
            p.print_help()
        else:
            raise UsageException("error: command %s not recognized" % cmd_name)

def fill_string(s, minlen):
    if len(s) < minlen:
        s += " " * (minlen - len(s))
    return s

def get_simple_usage(context):
    """Return simple usage as a string.

    Expects an HelpContext instance.
    """
    ret = [USAGE % {"name": "bentomaker",
                    "version": bento.__version__}]
    ret.append("Basic Commands:")

    commands = []

    def add_group(cmd_names):
        for name in cmd_names:
            doc = context.short_descriptions[name]
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

def command(f):
    """Decorator to create a new command from a simple function

    The function should take one CommandContext instance

    Example
    -------
 
    A simple command may be defined as follows::

        @command
        def hello(context):
            print "hello"
    """
    return WrappedCommand(f)

def find_hook_commands(modules):
    """Retrieve all command instances defined in given modules list.

    This should be used to find commands defined through the hook.command. This
    works by looking for all WrappedCommand instances in the modules.

    Parameters
    ----------
    modules: seq
        list of modules to look into
    """
    commands = []
    for module in modules:
        commands.extend([f for f in vars(module).values() if isinstance(f,
            WrappedCommand)])
    return commands
