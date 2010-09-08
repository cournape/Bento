#! /usr/bin/env python
import sys
import os
import re
import getopt
import optparse
import traceback

import bento

from bento.compat.api \
    import \
        relpath

from bento.core.utils import \
        subst_vars, pprint
from bento.core.platforms import \
        get_scheme
from bento.core.parser.api import \
        ParseError
from bento.core.package import \
        PackageDescription
from bento._config import \
        BENTO_SCRIPT
import bento.core.node

from bento.commands.core import \
        Command, HelpCommand, get_usage
from bento.commands.configure import \
        ConfigureCommand, get_configured_state
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
        get_command_names, get_command, \
        get_public_command_names
from bento.commands.errors import \
        ConvertionError, UsageException, CommandExecutionFailure

from bento.commands.hooks \
    import \
        get_pre_hooks, get_post_hooks, get_command_override
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
 
def dummy_startup():
    pass

def dummy_shutdown():
    pass

def set_main():
    import imp

    # Some commands work without a bento description file (convert, help)
    if not os.path.exists(BENTO_SCRIPT):
        return None
    pkg = PackageDescription.from_file(BENTO_SCRIPT)

    if pkg.hook_file is None:
        return None
    else:
        main_file = os.path.abspath(pkg.hook_file)
        if not os.path.exists(main_file):
            raise ValueError("Hook file %s not found" % main_file)

    module = imp.new_module("toysetup_module")
    module.__file__ = os.path.abspath(main_file)
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
    if argv is None:
        argv = sys.argv[1:]
    popts = parse_global_options(argv)
    cmd_name = popts["cmd_name"]
    if cmd_name and cmd_name in ["convert"]:
        _main(popts)
    else:
        _wrapped_main(popts)

def _wrapped_main(popts):
    mod = set_main()
    if mod:
        mod.startup()

    try:
        return _main(popts)
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
        cmd.run(Context(cmd, []))
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
            run_cmd(cmd_name, cmd_opts)

import yaku.context

# XXX: The yaku configure stuff is ugly, and introduces a lot of global state.
class Context(object):
    def __init__(self, cmd, cmd_opts, top_node):
        self.cmd = cmd
        self.cmd_opts = cmd_opts
        self.help = False
        self.top_node = top_node

    def get_package(self):
        state = get_configured_state()
        return state.pkg

    def get_user_data(self):
        state = get_configured_state()
        return state.user_data

    def store(self):
        pass

class ConfigureContext(Context):
    def __init__(self, cmd, cmd_opts, top_node):
        Context.__init__(self, cmd, cmd_opts, top_node)
        self.yaku_configure_ctx = yaku.context.get_cfg()

    def store(self):
        Context.store(self)
        self.yaku_configure_ctx.store()

class BuildContext(Context):
    def __init__(self, cmd, cmd_opts, top_node):
        Context.__init__(self, cmd, cmd_opts, top_node)
        self.yaku_build_ctx = yaku.context.get_bld()
        self._extensions_callback = {}
        self._clibraries_callback = {}
        self._clibrary_envs = {}
        self._extension_envs = {}

    def store(self):
        Context.store(self)
        self.yaku_build_ctx.store()

    def _compute_extension_name(self, extension_name):
        relpos = self.local_node.path_from(self.top_node)
        extension = relpos.replace(os.path.pathsep, ".")
        if extension:
            full_name = extension + ".%s" % extension_name
        else:
            full_name = extension_name
        return full_name

    # XXX: none of those register_* really belong here
    def register_builder(self, extension_name, builder):
        full_name = self._compute_extension_name(extension_name)
        self._extensions_callback[full_name] = builder

    def register_clib_builder(self, clib_name, builder):
        relpos = self.local_node.path_from(self.top_node)
        full_name = os.path.join(relpos, clib_name)
        self._clibraries_callback[full_name] = builder

    def register_environment(self, extension_name, env):
        full_name = self._compute_extension_name(extension_name)
        self._extension_envs[full_name] = env

    def register_clib_environment(self, clib_name, env):
        relpos = self.local_node.path_from(self.top_node)
        full_name = os.path.join(relpos, clib_name)
        self._clibrary_envs[full_name] = env

def run_cmd(cmd_name, cmd_opts):
    root = bento.core.node.Node("", None)
    top = root.find_dir(os.getcwd())

    cmd = get_command(cmd_name)()
    if get_command_override(cmd_name):
        cmd_funcs = get_command_override(cmd_name)
    else:
        cmd_funcs = [(cmd.run, top.abspath())]

    if cmd_name == "configure":
        ctx = ConfigureContext(cmd, cmd_opts, top)
    elif cmd_name == "build":
        ctx = BuildContext(cmd, cmd_opts, top)
    else:
        ctx = Context(cmd, cmd_opts, top)

    try:
        pkg = PackageDescription.from_file(BENTO_SCRIPT)
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
            for hook, local_dir in get_pre_hooks(cmd_name):
                set_local_ctx(ctx, hook, local_dir)

        while cmd_funcs:
            cmd_func, local_dir = cmd_funcs.pop(0)
            set_local_ctx(ctx, cmd_func, local_dir)

        if get_post_hooks(cmd_name) is not None:
            for hook, local_dir in get_post_hooks(cmd_name):
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
        pprint('RED',  msg % (SCRIPT_NAME, SCRIPT_NAME, e.__class__, str(e)))
        sys.exit(1)
    sys.exit(ret)

if __name__ == '__main__':
    noexc_main()
