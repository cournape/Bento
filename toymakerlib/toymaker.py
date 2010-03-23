#! /usr/bin/env python
import sys
import os
import getopt
import optparse
import traceback

import toydist

from toydist.core.utils import \
        subst_vars, pprint
from toydist.core.platforms import \
        get_scheme
from toydist.core.parser.api import \
        ParseError

from toydist.commands.core import \
        Command, HelpCommand, get_usage
from toydist.commands.configure import \
        ConfigureCommand
from toydist.commands.build import \
        BuildCommand
from toydist.commands.install import \
        InstallCommand
from toydist.commands.parse import \
        ParseCommand
from toydist.commands.convert import \
        ConvertCommand
from toydist.commands.sdist import \
        SdistCommand
from toydist.commands.detect_type import \
        DetectTypeCommand
from toydist.commands.build_pkg_info import \
        BuildPkgInfoCommand
from toydist.commands.build_egg import \
        BuildEggCommand
from toydist.commands.build_wininst import \
        BuildWininstCommand
from toydist.commands.core import \
        register_command, UsageException, \
        MyOptionParser, get_command_names, get_command, \
        get_public_command_names, ConvertionError

if os.environ.get("TOYMAKER_DEBUG", None) is not None:
    TOYMAKER_DEBUG = True
else:
    TOYMAKER_DEBUG = False

SCRIPT_NAME = 'toymaker'

#================================
#   Create the command line UI
#================================
register_command("help", HelpCommand)
register_command("configure", ConfigureCommand)
register_command("build", BuildCommand)
register_command("install", InstallCommand)
register_command("convert", ConvertCommand)
register_command("sdist", SdistCommand)
register_command("build_egg", BuildEggCommand)
register_command("build_wininst", BuildWininstCommand)

register_command("build_pkg_info", BuildPkgInfoCommand, public=False)
register_command("parse", ParseCommand, public=False)
register_command("detect_type", DetectTypeCommand, public=False)
 
def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    show_usage = False
    show_version = False
    show_full_version = False
    cmd_name = None
    cmd_opts = None

    try:
        opts, pargs = getopt.getopt(argv, "hv", ["help", "version", "full-version"])
        for opt, arg in opts:
            if opt in ("--help", "-h"):
                show_usage = True
            if opt in ("--version", "-v"):
                show_version = True
            if opt in ("--full-version"):
                show_full_version = True

        if len(pargs) > 0:
            cmd_name = pargs.pop(0)
            cmd_opts = pargs
    except getopt.GetoptError, e:
        emsg = "%s: illegal global option -- %s" % (SCRIPT_NAME, e.opt)
        print emsg
        print get_usage()
        return 1

    if show_version:
        print toydist.__version__
        return 0

    if show_full_version:
        print toydist.__version__ + "git" + toydist.__git_revision__
        return 0

    if show_usage:
        cmd = get_command('help')()
        cmd.run([])
        return 0

    if not cmd_name:
        print "Type '%s help' for usage." % SCRIPT_NAME
        return 1
    else:
        if not cmd_name in get_command_names():
            raise UsageException("%s: Error: unknown command %s" % (SCRIPT_NAME, cmd_name))
        else:
            cmd = get_command(cmd_name)()
            cmd.run(cmd_opts)

def noexc_main(argv=None):
    try:
        ret = main(argv)
    except UsageException, e:
        pprint('RED', e)
        sys.exit(1)
    except ParseError, e:
        pprint('RED', "".join(e.args))
        sys.exit(2)
    except ConvertionError, e:
        pprint('RED', "".join(e.args))
        sys.exit(3)
    except Exception, e:
        if TOYMAKER_DEBUG:
            tb = sys.exc_info()[2]
            traceback.print_tb(tb)
        pprint('RED', "%s: Error: %s crashed (uncaught exception %s: %s).\n"
                "Please report this on toydist issue tracker: \n" \
                "\thttp://github.com/cournape/toydist/issues" %
               (SCRIPT_NAME, SCRIPT_NAME, e.__class__, str(e)))
        sys.exit(1)
    sys.exit(ret)

if __name__ == '__main__':
    noexc_main()
