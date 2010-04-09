import getopt
import optparse
import copy

# FIXME: how to handle script name in one location
SCRIPT_NAME = 'toymaker'

USAGE = """\
%(name)s [command] [options]

Main commands:
%(cmds)s\
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

class UsageException(Exception):
    pass

class ConvertionError(Exception):
    pass

class MyOptionParser(optparse.OptionParser):
    def __init__(self, *a, **kw):
        if not kw.has_key('add_help_option'):
            kw['add_help_option'] = False
        optparse.OptionParser.__init__(self, *a, **kw)

    def error(self, msg):
        raise UsageException("%s: ERROR: %s" % (SCRIPT_NAME, msg))

class Command(object):
    long_descr = None
    short_descr = None
    # XXX: decide how to deal with subcommands options
    opts = [{'opts': ['-h', '--help'], "help": "Show this message and exits.",
                                       "action": "store_true"}]

    def __init__(self):
        self.parser = None

    def set_option_parser(self):
        try:
            parser = MyOptionParser(self.long_descr.splitlines()[1])
            oo = copy.deepcopy(self.opts)
            for o in oo:
                a = o.pop('opts')
                kw = o
                parser.add_option(*a, **kw)
            self.parser = parser
        except getopt.GetoptError, e:
            raise UsageException("%s: error: %s for help subcommand" % (SCRIPT_NAME, e))

    def run(self, opts):
        raise NotImplementedError("run method should be implemented by command classes.")

class HelpCommand(Command):
    long_descr = """\
Purpose: Show help on a command or other topic.
Usage:   toymaker help [TOPIC] or toymaker help [COMMAND]."""
    short_descr = "gives help on a given topic or command."
    def run(self, cmd_args):
        if len(cmd_args) < 1:
            print get_usage()
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
            parser = MyOptionParser()
            for o in self.opts:
                kw = o.copy()
                a = kw.pop('opts')
                parser.add_option(*a, **kw)
            parser.parse_args(help_args)
        except optparse.OptionError, e:
            raise UsageException("%s: error: %s for help subcommand" % (SCRIPT_NAME, e))

        # 
        if not cmd_name in get_command_names():
            raise UsageException("%s: error: %s not recognized" % (SCRIPT_NAME, cmd_name))
        cmd_class = get_command(cmd_name)

        parser = MyOptionParser(usage='')
        for o in cmd_class.opts:
            a = o.pop('opts')
            kw = o
            parser.add_option(*a, **kw)
        print cmd_class.long_descr
        print ""
        parser.print_help()

def get_usage():
    cmd_help = []
    cmd_doc = {}
    cmd_names = sorted(get_public_command_names())

    for name in cmd_names:
        v = get_command(name)
        doc = v.short_descr
        if doc is None:
            doc = "undocumented"
        cmd_doc[name] = doc

    just = max([len(name) for name in cmd_names])

    cmd_help = ['  %s: %s' % (name.ljust(just), cmd_doc[name]) for name in cmd_names]
    return USAGE % {'cmds': "\n".join(cmd_help), 'name': SCRIPT_NAME}
