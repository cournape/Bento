#! /usr/bin/env python
import time
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
        BENTO_SCRIPT, BUILD_DIR
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
        COMMANDS_REGISTRY
from bento.commands.errors import \
        ConvertionError, UsageException, CommandExecutionFailure
from bento.commands.dependency \
    import \
        CommandScheduler, CommandDataProvider

from bento.commands.hooks \
    import \
        get_pre_hooks, get_post_hooks, get_command_override, create_hook_module
from bento.commands.context \
    import \
        CmdContext, BuildYakuContext, ConfigureYakuContext, CONTEXT_REGISTRY
import bento.core.errors

if os.environ.get("BENTOMAKER_DEBUG", "0") != "0":
    BENTOMAKER_DEBUG = True
else:
    BENTOMAKER_DEBUG = False

SCRIPT_NAME = 'bentomaker'

CMD_SCHEDULER = CommandScheduler()
CMD_SCHEDULER.set_before(BuildCommand, ConfigureCommand)
CMD_SCHEDULER.set_before(BuildEggCommand, BuildCommand)
CMD_SCHEDULER.set_before(BuildWininstCommand, BuildCommand)
CMD_SCHEDULER.set_before(InstallCommand, BuildCommand)

CMD_DATA_DUMP = os.path.join(BUILD_DIR, "cmd_data.db")
CMD_DATA_STORE = CommandDataProvider.from_file(CMD_DATA_DUMP)

#================================
#   Create the command line UI
#================================
def register_commands():
    COMMANDS_REGISTRY.register_command("help", HelpCommand)
    COMMANDS_REGISTRY.register_command("configure", ConfigureCommand)
    COMMANDS_REGISTRY.register_command("build", BuildCommand)
    COMMANDS_REGISTRY.register_command("install", InstallCommand)
    COMMANDS_REGISTRY.register_command("convert", ConvertCommand)
    COMMANDS_REGISTRY.register_command("sdist", SdistCommand)
    COMMANDS_REGISTRY.register_command("build_egg", BuildEggCommand)
    COMMANDS_REGISTRY.register_command("build_wininst", BuildWininstCommand)
    COMMANDS_REGISTRY.register_command("distcheck", DistCheckCommand)

    COMMANDS_REGISTRY.register_command("build_pkg_info", BuildPkgInfoCommand, public=False)
    COMMANDS_REGISTRY.register_command("parse", ParseCommand, public=False)
    COMMANDS_REGISTRY.register_command("detect_type", DetectTypeCommand, public=False)
 
def register_command_contexts():
    CONTEXT_REGISTRY.set_default(CmdContext)
    if not CONTEXT_REGISTRY.is_registered("configure"):
        CONTEXT_REGISTRY.register("configure", ConfigureYakuContext)
    if not CONTEXT_REGISTRY.is_registered("build"):
        CONTEXT_REGISTRY.register("build", BuildYakuContext)

def set_main():
    # Some commands work without a bento description file (convert, help)
    if not os.path.exists(BENTO_SCRIPT):
        return []

    pkg = CachedPackage.get_package(BENTO_SCRIPT)
    #create_package_description(BENTO_SCRIPT)

    modules = []
    for f in pkg.hook_files:
        main_file = os.path.abspath(f)
        if not os.path.exists(main_file):
            raise ValueError("Hook file %s not found" % main_file)
        modules.append(create_hook_module(f))
    return modules

def main(argv=None):
    if hasattr(os, "getuid"):
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
    register_command_contexts()

    if popts["show_version"]:
        print bento.__version__
        return 0

    if popts["show_full_version"]:
        print bento.__version__ + "git" + bento.__git_revision__
        return 0

    if popts["show_usage"]:
        cmd = COMMANDS_REGISTRY.get_command('help')()
        cmd.run(CmdContext(cmd, [], None, None))
        return 0

    cmd_name = popts["cmd_name"]
    cmd_opts = popts["cmd_opts"]

    if not cmd_name:
        print "Type '%s help' for usage." % SCRIPT_NAME
        return 1
    else:
        if not cmd_name in COMMANDS_REGISTRY.get_command_names():
            raise UsageException("%s: Error: unknown command %s" % (SCRIPT_NAME, cmd_name))
        else:
            run_cmd(cmd_name, cmd_opts)

def _get_package_with_user_flags(cmd_name, cmd_opts):
    if cmd_name == "configure":
        from bento.commands.configure import get_flag_values
        cmd = COMMANDS_REGISTRY.get_command(cmd_name)()
        flag_values = get_flag_values(cmd, cmd_opts)
    else:
        flag_values = None
    return CachedPackage.get_package(BENTO_SCRIPT, flag_values)

def _get_subpackage(pkg, top, local_node):
    rpath = local_node.path_from(top)
    k = os.path.join(rpath, "bento.info")
    if local_node == top:
        return pkg
    else:
        if k in pkg.subpackages:
            return pkg.subpackages[k]
        else:
            return None

def run_dependencies(cmd_klass, top, pkg):
    deps = CMD_SCHEDULER.order(cmd_klass)
    for cmd_klass in deps:
        cmd_name = COMMANDS_REGISTRY.get_command_name(cmd_klass)
        cmd_argv = CMD_DATA_STORE.get_argv(cmd_name)
        ctx_klass = CONTEXT_REGISTRY.get(cmd_name)
        run_cmd_in_context(cmd_klass, cmd_name, cmd_argv, ctx_klass, top, pkg)

def is_help_only(cmd_klass, cmd_argv):
    cmd = cmd_klass()
    o, a = cmd.options_context.parser.parse_args(cmd_argv)
    if o.help:
        return True
    else:
        return False

def run_cmd(cmd_name, cmd_opts):
    root = bento.core.node.Node("", None)
    top = root.find_dir(os.getcwd())

    cmd_klass = COMMANDS_REGISTRY.get_command(cmd_name)
    # XXX: fix this special casing
    if cmd_name in ["help", "convert"]:
        cmd = cmd_klass()
        ctx_klass = CONTEXT_REGISTRY.get(cmd_name)
        ctx = ctx_klass(cmd, cmd_opts, None, top)
        cmd.run(ctx)
        return

    if not os.path.exists(BENTO_SCRIPT):
        raise UsageException("Error: no %s found !" % BENTO_SCRIPT)

    pkg = _get_package_with_user_flags(cmd_name, cmd_opts)
    if is_help_only(cmd_klass, cmd_opts):
        ctx_klass = CONTEXT_REGISTRY.get(cmd_name)
        run_cmd_in_context(cmd_klass, cmd_name, cmd_opts, ctx_klass, top, pkg)
    else:
        run_dependencies(cmd_klass, top, pkg)

        ctx_klass = CONTEXT_REGISTRY.get(cmd_name)
        run_cmd_in_context(cmd_klass, cmd_name, cmd_opts, ctx_klass, top, pkg)

        CMD_DATA_STORE.set(cmd_name, cmd_opts)
        CMD_DATA_STORE.store(CMD_DATA_DUMP)

def run_cmd_in_context(cmd_klass, cmd_name, cmd_opts, ctx_klass, top, pkg):
    """Run the given Command instance inside its context, including any hook
    and/or override."""
    cmd = cmd_klass()
    ctx = ctx_klass(cmd, cmd_opts, pkg, top)
    if get_command_override(cmd_name):
        cmd_funcs = get_command_override(cmd_name)
    else:
        cmd_funcs = [(cmd.run, top.abspath())]

    try:
        def set_local_ctx(ctx, local_dir):
            local_node = top.find_dir(relpath(local_dir, top.abspath()))
            spkg = _get_subpackage(pkg, top, local_node)
            ctx.local_dir = local_dir
            ctx.local_node = local_node
            ctx.top_node = top
            ctx.local_pkg = spkg
            ctx.pkg = pkg

        if get_pre_hooks(cmd_name) is not None:
            for hook, local_dir, help_bypass in get_pre_hooks(cmd_name):
                if not ctx.help and help_bypass:
                    set_local_ctx(ctx, local_dir)
                    hook(ctx)

        while cmd_funcs:
            cmd_func, local_dir = cmd_funcs.pop(0)
            set_local_ctx(ctx, local_dir)
            cmd_func(ctx)

        if get_post_hooks(cmd_name) is not None:
            for hook, local_dir, help_bypass in get_post_hooks(cmd_name):
                if not ctx.help and help_bypass:
                    set_local_ctx(ctx, local_dir)
                    hook(ctx)

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
