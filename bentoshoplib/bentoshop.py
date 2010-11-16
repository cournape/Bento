import os
import sys
import getopt
import traceback

from bento.core.utils \
    import \
        subst_vars, pprint
from bentoshoplib.commands \
    import \
        CommandRegistry, Install, Uninstall, Help, InitDb, List
from bentoshoplib._config \
    import \
        SCRIPT_NAME

if os.environ.get("BENTOSHOP_DEBUG", "0") != "0":
    BENTOSHOP_DEBUG = True
else:
    BENTOSHOP_DEBUG = False

class UsageException(Exception):
    pass

REGISTRY = CommandRegistry()
REGISTRY.register_command("install", Install)
REGISTRY.register_command("uninstall", Uninstall)
REGISTRY.register_command("init_db", InitDb)
REGISTRY.register_command("list", List)

def parse_global_options(argv):
    ret = {"cmd_name": None, "cmd_opts": None,
           "show_usage": False}

    try:
        opts, pargs = getopt.getopt(argv, "h", ["help"])
        for opt, arg in opts:
            if opt in ("--help", "-h"):
                ret["show_usage"] = True
            if opt in ("--version", "-v"):
                ret["show_version"] = True
            if opt in ("--full-version"):
                ret["show_full_version"] = True

        if len(pargs) > 0:
            ret["cmd_name"] = pargs.pop(0)
            ret["cmd_opts"] = pargs
    except getopt.GetoptError, e:
        emsg = "%s: illegal global option: %r" % (SCRIPT_NAME, e.opt)
        raise UsageException(emsg)

    return ret

def setup_option_parser():
    parser = argparse.ArgumentParser(prog=SCRIPT_NAME)
    subparsers = parser.add_subparsers()

    for cmd_name in REGISTRY.command_names():
        cmd_parser = subparsers.add_parser(cmd_name)

    return parser

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    popts = parse_global_options(argv)
    cmd_name = popts["cmd_name"]
    if cmd_name == "help":
        cmd = Help(REGISTRY)
        cmd.run()
    elif cmd_name:
        cmd_klass = REGISTRY.command(cmd_name)
        cmd = cmd_klass()
        cmd.run(popts["cmd_opts"])
    else:
        print "Type %s help for usage" % SCRIPT_NAME
        return 1

def noexc_main(argv=None):
    def _print_debug():
        if BENTOSHOP_DEBUG:
            tb = sys.exc_info()[2]
            traceback.print_tb(tb)
    try:
        ret = main(argv)
    except Exception, e:
        msg = """\
%s: Error: %s crashed (uncaught exception %s: %s).
Please report this on bento issue tracker:
    http://github.com/cournape/bento/issues"""
        if not BENTOSHOP_DEBUG:
            msg += "\nYou can get a full traceback by setting BENTOSHOP_DEBUG=1"
        else:
            _print_debug()
        pprint('RED',  msg % (SCRIPT_NAME, SCRIPT_NAME, e.__class__, str(e)))
        sys.exit(1)
