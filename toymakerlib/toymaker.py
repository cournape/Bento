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
from toydist.core.package import \
        PackageDescription
from toydist._config import \
        TOYDIST_SCRIPT

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
from toydist.commands.distcheck import \
        DistCheckCommand
from toydist.commands.core import \
        register_command, \
        get_command_names, get_command, \
        get_public_command_names
from toydist.commands.errors import \
        ConvertionError, UsageException, CommandExecutionFailure

from toydist.commands.hooks \
    import \
        get_pre_hooks, get_post_hooks, get_command_override

if os.environ.get("TOYMAKER_DEBUG", None) is not None:
    TOYMAKER_DEBUG = True
else:
    TOYMAKER_DEBUG = False

SCRIPT_NAME = 'toymaker'

#================================
#   Create the command line UI
#================================
def register_commands():
    register_command("help", HelpCommand)
    register_command("configure", ConfigureCommand)
    register_command("build", BuildCommand)
    register_command("install", InstallCommand)
    register_command("convert", ConvertCommand)
    register_command("sdist", SdistCommand)
    register_command("build_egg", BuildEggCommand)
    register_command("build_wininst", BuildWininstCommand)
    register_command("distcheck", DistCheckCommand)

    register_command("build_pkg_info", BuildPkgInfoCommand, public=False)
    register_command("parse", ParseCommand, public=False)
    register_command("detect_type", DetectTypeCommand, public=False)
 
def dummy_startup():
    pass

def dummy_shutdown():
    pass

def set_main():
    import imp

    pkg = PackageDescription.from_file(TOYDIST_SCRIPT)
    main_file = pkg.hook_file

    #main_file = "toysetup.py"
    if main_file is None:
        return None
    else:
        if not os.path.exists(main_file):
            raise ValueError("Hook file %s not found" % main_file)

    module = imp.new_module("toysetup_module")
    code = open(main_file).read()

    sys.path.insert(0, os.path.dirname(main_file))
    try:
        exec(compile(code, main_file, 'exec'), module.__dict__)
    finally:
        sys.path.pop(0)

    module.root_path = main_file
    if not hasattr(module, "startup"):
        module.startup = dummy_startup
    if not hasattr(module, "shutdown"):
        module.shutdown = dummy_shutdown

    return module

def main(argv=None):
    mod = set_main()
    if mod:
        mod.startup()

    try:
        return _main(argv)
    finally:
        if mod:
            mod.shutdown()

def parse_global_options(argv):
    ret = {"cmd_name": None, "cmd_opts": None,
           "show_version": False, "show_full_version": False,
           "show_usage": False}

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
            ret["cmd_name"] = pargs.pop(0)
            ret["cmd_opts"] = pargs
    except getopt.GetoptError, e:
        emsg = "%s: illegal global option: %r" % (SCRIPT_NAME, e.opt)
        raise UsageException(emsg)

    return ret

def _main(argv=None):
    register_commands()

    if argv is None:
        argv = sys.argv[1:]

    ret = parse_global_options(argv)
    if ret["show_version"]:
        print toydist.__version__
        return 0

    if ret["show_full_version"]:
        print toydist.__version__ + "git" + toydist.__git_revision__
        return 0

    if ret["show_usage"]:
        cmd = get_command('help')()
        cmd.run([])
        return 0

    cmd_name = ret["cmd_name"]
    cmd_opts = ret["cmd_opts"]

    if not cmd_name:
        print "Type '%s help' for usage." % SCRIPT_NAME
        return 1
    else:
        if not cmd_name in get_command_names():
            raise UsageException("%s: Error: unknown command %s" % (SCRIPT_NAME, cmd_name))
        else:
            run_cmd(cmd_name, cmd_opts)

def run_cmd(cmd_name, cmd_opts):
    if get_command_override(cmd_name):
        cmd_func = get_command_override(cmd_name)[0]
    else:
        cmd = get_command(cmd_name)()
        cmd_func = cmd.run

    if get_pre_hooks(cmd_name) is not None:
        for f, a, kw in get_pre_hooks(cmd_name):
            f(*a, **kw)
    cmd_func(cmd_opts)
    if get_post_hooks(cmd_name) is not None:
        for f, a, kw in get_post_hooks(cmd_name):
            f(*a, **kw)

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
    except CommandExecutionFailure, e:
        pprint('RED', "".join(e.args))
        sys.exit(4)
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
