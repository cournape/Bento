#! /usr/bin/env python
import sys
import os
import getopt
import traceback

import bento

from bento.compat.api \
    import \
        relpath

from bento.core.utils import \
        pprint
from bento.core.parser.api import \
        ParseError
from bento.core.package_cache import \
        CachedPackage
from bento._config import \
        BENTO_SCRIPT
import bento.core.node

from bento.commands.core import \
        HelpCommand
from bento.commands.configure import \
        ConfigureCommand
from bento.commands.build import \
        BuildCommand
from bento.commands.install import \
        InstallCommand
from bento.commands.parse import \
        ParseCommand
from bento.commands.convert import \
        ConvertCommand
from bento.commands.sdist import \
        SdistCommand
from bento.commands.detect_type import \
        DetectTypeCommand
from bento.commands.build_pkg_info import \
        BuildPkgInfoCommand
from bento.commands.build_egg import \
        BuildEggCommand
from bento.commands.build_wininst import \
        BuildWininstCommand
from bento.commands.distcheck import \
        DistCheckCommand
from bento.commands.core import \
        register_command, \
        get_command_names, get_command
from bento.commands.errors import \
        ConvertionError, UsageException, CommandExecutionFailure

from bento.commands.hooks \
    import \
        get_pre_hooks, get_post_hooks, get_command_override, create_hook_module
from bento.commands.context \
    import \
        CmdContext, BuildContext, ConfigureContext
import bento.core.errors

if os.environ.get("BENTOMAKER_DEBUG", "0") != "0":
    BENTOMAKER_DEBUG = True
else:
    BENTOMAKER_DEBUG = False

SCRIPT_NAME = 'bentomaker'

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
 
def set_main():
    # Some commands work without a bento description file (convert, help)
    if not os.path.exists(BENTO_SCRIPT):
        return []

    pkg_cache = CachedPackage()
    try:
        pkg = pkg_cache.get_package(BENTO_SCRIPT)
    finally:
        pkg_cache.close()
    #create_package_description(BENTO_SCRIPT)

    modules = []
    for f in pkg.hook_files:
        main_file = os.path.abspath(f)
        if not os.path.exists(main_file):
            raise ValueError("Hook file %s not found" % main_file)
        modules.append(create_hook_module(f))
    return modules

def main(argv=None):
    if os.getuid() == 0:
        pprint("RED", "Using bentomaker under root/sudo is *strongly* discouraged - do you want to continue ? y/N")
        ans = raw_input()
        if not ans.lower() in ["y", "yes"]:
            raise UsageException("bentomaker execution canceld (not using bentomaker with admin privileges)")
    if argv is None:
        argv = sys.argv[1:]
    popts = parse_global_options(argv)
    cmd_name = popts["cmd_name"]
    if cmd_name and cmd_name not in ["convert"]:
        _wrapped_main(popts)
    else:
        _main(popts)

def _wrapped_main(popts):
    mods = set_main()
    for mod in mods:
        mod.startup()

    try:
        return _main(popts)
    finally:
        for mod in mods:
            mod.shutdown()

def parse_global_options(argv):
    ret = {"cmd_name": None, "cmd_opts": None,
           "show_version": False, "show_full_version": False,
           "show_usage": False}

    try:
        opts, pargs = getopt.getopt(argv, "hv", ["help", "version", "full-version"])
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

def _main(popts):
    register_commands()

    if popts["show_version"]:
        print bento.__version__
        return 0

    if popts["show_full_version"]:
        print bento.__version__ + "git" + bento.__git_revision__
        return 0

    if popts["show_usage"]:
        cmd = get_command('help')()
        cmd.run(CmdContext(cmd, [], None, None))
        return 0

    cmd_name = popts["cmd_name"]
    cmd_opts = popts["cmd_opts"]

    if not cmd_name:
        print "Type '%s help' for usage." % SCRIPT_NAME
        return 1
    else:
        if not cmd_name in get_command_names():
            raise UsageException("%s: Error: unknown command %s" % (SCRIPT_NAME, cmd_name))
        else:
            check_command_dependencies(cmd_name)
            run_cmd(cmd_name, cmd_opts)

from bento.commands.context \
    import \
        _read_argv_checksum

def check_command_dependencies(cmd_name):
    # FIXME: temporary hack to inform the user, handle command dependency
    # automatically at some point
    if cmd_name == "build":
        configure_cmd = get_command("configure")
        if not configure_cmd.has_run():
            raise UsageException("""\
The project was not configured: you need to run 'bentomaker configure' first""")
        if not configure_cmd.up_to_date():
            raise UsageException("""\
The project configuration has changed. You need to re-run 'bentomaker configure' first""")
    elif cmd_name in ["install", "build_egg", "build_wininst"]:
        build_cmd = get_command("build")
        if not build_cmd.has_run():
            raise UsageException("""\
The project was not built: you need to 'bentomaker build' first""")
        built_config = _read_argv_checksum("build")
        configured_config = _read_argv_checksum("configure")
        if built_config != configured_config:
            raise UsageException("""\
The project was reconfigured: you need to re-run 'bentomaker build' before \
installing""")

def run_cmd(cmd_name, cmd_opts):
    root = bento.core.node.Node("", None)
    top = root.find_dir(os.getcwd())

    cmd = get_command(cmd_name)()
    if get_command_override(cmd_name):
        cmd_funcs = get_command_override(cmd_name)
    else:
        cmd_funcs = [(cmd.run, top.abspath())]

    if not os.path.exists(BENTO_SCRIPT):
        raise UsageException("Error: no %s found !" % BENTO_SCRIPT)

    pkg_cache = CachedPackage()
    try:
        package_options = pkg_cache.get_options(BENTO_SCRIPT)
    finally:
        pkg_cache.close()
    cmd.setup_options_parser(package_options)

    if cmd_name == "configure":
        # FIXME: this whole dance to get the user-given flag values is insane
        from bento.commands.configure import set_flag_options
        o, a = cmd.parser.parse_args(cmd_opts)
        flag_values = set_flag_options(cmd.flag_opts, o)
    else:
        flag_values = None
    pkg_cache = CachedPackage()
    try:
        pkg = pkg_cache.get_package(BENTO_SCRIPT, flag_values)
    finally:
        pkg_cache.close()

    if cmd_name == "configure":
        ctx = ConfigureContext(cmd, cmd_opts, pkg, top)
    elif cmd_name == "build":
        ctx = BuildContext(cmd, cmd_opts, pkg, top)
    else:
        ctx = CmdContext(cmd, cmd_opts, pkg, top)

    try:
        spkgs = pkg.subpackages

        def get_subpackage(local_node):
            rpath = local_node.path_from(top)
            k = os.path.join(rpath, "bento.info")
            if local_node == top:
                return pkg
            else:
                if k in spkgs:
                    return spkgs[k]
                else:
                    return None
        def set_local_ctx(ctx, hook, local_dir):
            local_node = top.find_dir(
                    relpath(local_dir, top.abspath()))
            spkg = get_subpackage(local_node)
            ctx.local_dir = local_dir
            ctx.local_node = local_node
            ctx.top_node = top
            ctx.local_pkg = spkg
            ctx.pkg = pkg
            return hook(ctx)

        if get_pre_hooks(cmd_name) is not None:
            for hook, local_dir, help_bypass in get_pre_hooks(cmd_name):
                if not ctx.help and help_bypass:
                    set_local_ctx(ctx, hook, local_dir)

        while cmd_funcs:
            cmd_func, local_dir = cmd_funcs.pop(0)
            set_local_ctx(ctx, cmd_func, local_dir)

        if get_post_hooks(cmd_name) is not None:
            for hook, local_dir, help_bypass in get_post_hooks(cmd_name):
                if not ctx.help and help_bypass:
                    set_local_ctx(ctx, hook, local_dir)
        cmd.shutdown(ctx)
    finally:
        ctx.store()

def noexc_main(argv=None):
    def _print_debug():
        if BENTOMAKER_DEBUG:
            tb = sys.exc_info()[2]
            traceback.print_tb(tb)
    try:
        ret = main(argv)
    except UsageException, e:
        _print_debug()
        pprint('RED', e)
        sys.exit(1)
    except ParseError, e:
        _print_debug()
        pprint('RED', str(e))
        sys.exit(2)
    except ConvertionError, e:
        _print_debug()
        pprint('RED', "".join(e.args))
        sys.exit(3)
    except CommandExecutionFailure, e:
        _print_debug()
        pprint('RED', "".join(e.args))
        sys.exit(4)
    except bento.core.errors.BuildError, e:
        _print_debug()
        pprint('RED', e)
        sys.exit(8)
    except bento.core.errors.InvalidPackage, e:
        _print_debug()
        pprint('RED', e)
        sys.exit(16)
    except Exception, e:
        msg = """\
%s: Error: %s crashed (uncaught exception %s: %s).
Please report this on bento issue tracker:
    http://github.com/cournape/bento/issues"""
        if not BENTOMAKER_DEBUG:
            msg += "\nYou can get a full traceback by setting BENTOMAKER_DEBUG=1"
        else:
            _print_debug()
        pprint('RED',  msg % (SCRIPT_NAME, SCRIPT_NAME, e.__class__, str(e)))
        sys.exit(1)
    sys.exit(ret)

if __name__ == '__main__':
    noexc_main()
