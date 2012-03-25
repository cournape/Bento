#! /usr/bin/env python
#import demandimport
#demandimport.enable()
import sys
import os
import traceback

import bento

from bento.core.utils \
    import \
        pprint, extract_exception
from bento.core.parser.api \
    import \
        ParseError
from bento._config \
    import \
        BENTO_SCRIPT, DB_FILE, _SUB_BUILD_DIR
from bento.core \
    import \
        PackageDescription
import bento.core.node

from bento.commands.api \
    import \
        HelpCommand, ConfigureCommand, BuildCommand, InstallCommand, \
        ParseCommand, SdistCommand, BuildPkgInfoCommand, BuildEggCommand, \
        BuildWininstCommand, UsageException, CommandExecutionFailure
from bento.commands.core \
    import \
        find_hook_commands, CommandRegistry
from bento.commands.dependency \
    import \
        CommandScheduler, CommandDataProvider
from bento.commands.options \
    import \
        OptionsRegistry, OptionsContext, Option

from bento.commands.hooks \
    import \
        find_pre_hooks, find_post_hooks, create_hook_module
from bento.commands.context \
    import \
        CmdContext, BuildYakuContext, ConfigureYakuContext, ContextRegistry, \
        HelpContext, GlobalContext, SdistContext
from bento.commands.wrapper_utils \
    import \
        run_cmd_in_context
from bento.convert.api \
    import \
        ConvertCommand, DetectTypeCommand, ConvertionError
import bento.core.errors

from bentomakerlib.package_cache \
    import \
        CachedPackage
from bentomakerlib.help \
    import \
        get_usage

if os.environ.get("BENTOMAKER_DEBUG", "0") != "0":
    BENTOMAKER_DEBUG = True
else:
    BENTOMAKER_DEBUG = False

SCRIPT_NAME = 'bentomaker'

CONTEXT_REGISTRY = ContextRegistry()

CMD_SCHEDULER = CommandScheduler()
CMD_SCHEDULER.set_before("build", "configure")
CMD_SCHEDULER.set_before("build_egg", "build")
CMD_SCHEDULER.set_before("build_wininst", "build")
CMD_SCHEDULER.set_before("install", "build")

# Path relative to build directory
CMD_DATA_DUMP = os.path.join(_SUB_BUILD_DIR, "cmd_data.db")

# FIXME: those private functions hiding global variables are horrible - they
# are a dirty workaround until a better solution to pass nodes to the
# underlying implementation is found (Node instances can only be created once
# the source and build directories are known)
__CMD_DATA_STORE = None
def _get_cmd_data_provider(dump_node):
    global __CMD_DATA_STORE
    if __CMD_DATA_STORE is None:
        __CMD_DATA_STORE = CommandDataProvider.from_file(dump_node.abspath())
    return __CMD_DATA_STORE

def _set_cmd_data_provider(cmd_name, cmd_argv, dump_node):
    global __CMD_DATA_STORE
    if __CMD_DATA_STORE is None:
        _get_cmd_data_provider(dump_node)
    __CMD_DATA_STORE.set(cmd_name, cmd_argv)
    __CMD_DATA_STORE.store(dump_node.abspath())

OPTIONS_REGISTRY = OptionsRegistry()

__CACHED_PACKAGE = None
def _set_cached_package(node):
    global __CACHED_PACKAGE
    if __CACHED_PACKAGE is not None:
        raise ValueError("Global cached package already set !")
    else:
        __CACHED_PACKAGE = CachedPackage(node)
        return __CACHED_PACKAGE

def _get_cached_package():
    global __CACHED_PACKAGE
    if __CACHED_PACKAGE is None:
        raise ValueError("Global cached package not set yet !")
    else:
        return __CACHED_PACKAGE

__PACKAGE_OPTIONS = None
def __get_package_options(top_node):
    global __PACKAGE_OPTIONS
    if __PACKAGE_OPTIONS:
        return __PACKAGE_OPTIONS
    else:
        n = top_node.find_node(BENTO_SCRIPT)
        __PACKAGE_OPTIONS = _get_cached_package().get_options(n.abspath())
        return __PACKAGE_OPTIONS

#================================
#   Create the command line UI
#================================
def register_commands(global_context):
    global_context.register_command("help", HelpCommand())
    global_context.register_command("configure", ConfigureCommand())
    global_context.register_command("build", BuildCommand())
    global_context.register_command("install", InstallCommand())
    global_context.register_command("convert", ConvertCommand())
    global_context.register_command("sdist", SdistCommand())
    global_context.register_command("build_egg", BuildEggCommand())
    global_context.register_command("build_wininst", BuildWininstCommand())

    global_context.register_command("build_pkg_info", BuildPkgInfoCommand(), public=False)
    global_context.register_command("parse", ParseCommand(), public=False)
    global_context.register_command("detect_type", DetectTypeCommand(), public=False)
 
    if sys.platform == "darwin":
        import bento.commands.build_mpkg
        global_context.register_command("build_mpkg",
            bento.commands.build_mpkg.BuildMpkgCommand(), public=False)
        global_context.set_before("build_mpkg", "build")

def register_options(global_context, cmd_name):
    cmd_klass = global_context.retrieve_command(cmd_name)
    usage = cmd_klass.long_descr.splitlines()[1]
    context = OptionsContext.from_command(cmd_klass, usage=usage)
    OPTIONS_REGISTRY.register(cmd_name, context)

def register_options_special(global_context):
    # Register options for special topics not attached to a "real" command
    # (e.g. 'commands')
    context = OptionsContext()
    def print_usage():
        print(get_usage(global_context))
    context.parser.print_help = print_usage
    OPTIONS_REGISTRY.register("commands", context)

    context = OptionsContext()
    def print_help():
        global_options = OPTIONS_REGISTRY.retrieve("")
        p = global_options.parser
        return(p.print_help())
    context.parser.print_help = print_help
    OPTIONS_REGISTRY.register("globals", context)

def register_command_contexts():
    CONTEXT_REGISTRY.set_default(CmdContext)
    if not CONTEXT_REGISTRY.is_registered("configure"):
        CONTEXT_REGISTRY.register("configure", ConfigureYakuContext)
    if not CONTEXT_REGISTRY.is_registered("build"):
        CONTEXT_REGISTRY.register("build", BuildYakuContext)
    if not CONTEXT_REGISTRY.is_registered("sdist"):
        CONTEXT_REGISTRY.register("sdist", SdistContext)
    if not CONTEXT_REGISTRY.is_registered("help"):
        CONTEXT_REGISTRY.register("help", HelpContext)

# All the global state/registration stuff goes here
def register_stuff(global_context):
    register_commands(global_context)
    for cmd_name in global_context.command_names():
        register_options(global_context, cmd_name)
    register_options_special(global_context)
    register_command_contexts()

def set_main(top_node, build_node):
    # Some commands work without a bento description file (convert, help)
    # FIXME: this should not be called here then - clearly separate commands
    # which require bento.info from the ones who do not
    n = top_node.find_node(BENTO_SCRIPT)
    if n is None:
        return []

    _set_cached_package(build_node.make_node(DB_FILE))

    pkg = _get_cached_package().get_package(n)
    #create_package_description(BENTO_SCRIPT)

    modules = []
    hook_files = pkg.hook_files
    for name, spkg in pkg.subpackages.items():
        hook_files.extend([os.path.join(spkg.rdir, h) for h in spkg.hook_files])
    # TODO: find doublons
    for f in hook_files:
        hook_node = top_node.make_node(f)
        if hook_node is None or not os.path.exists(hook_node.abspath()):
            raise ValueError("Hook file %s not found" % f)
        modules.append(create_hook_module(hook_node.abspath()))
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

    # FIXME: top_node vs srcnode
    source_root = os.path.join(os.getcwd(), os.path.dirname(popts["bento_info"]))
    build_root = os.path.join(os.getcwd(), popts["build_directory"])

    # FIXME: create_root_with_source_tree should return source node and build
    # node so that we don't have to find them and take the risk of
    # inconsistency
    root = bento.core.node.create_root_with_source_tree(source_root, build_root)
    run_node = root.find_node(os.getcwd())
    top_node = root.find_node(source_root)
    build_node = root.find_node(build_root)
    if run_node != top_node and run_node.is_src():
        raise UsageException("You cannot execute bentomaker in a subdirectory of the source tree !")
    if run_node != build_node and run_node.is_bld():
        raise UsageException("You cannot execute bentomaker in a subdirectory of the build tree !")

    global_context = GlobalContext(CommandRegistry(), CONTEXT_REGISTRY,
                                   OPTIONS_REGISTRY, CMD_SCHEDULER)
    if cmd_name and cmd_name not in ["convert"] or not cmd_name:
        return _wrapped_main(global_context, popts, run_node, top_node, build_node)
    else:
        register_stuff(global_context)
        return _main(global_context, popts, run_node, top_node, build_node)

def _wrapped_main(global_context, popts, run_node, top_node, build_node):
    def _big_ugly_hack():
        # FIXME: huge ugly hack - we need to specify once and for all when the
        # package info is parsed and available, so that we can define options
        # and co for commands
        from bento.commands.configure import _setup_options_parser
        # FIXME: logic to handle codepaths which work without a bento.info
        # should be put in one place
        n = top_node.find_node(BENTO_SCRIPT)
        if n:
            package_options = __get_package_options(top_node)
            _setup_options_parser(OPTIONS_REGISTRY.retrieve("configure"), package_options)
        else:
            import warnings
            warnings.warn("No %r file in current directory - not all options "
                          "will be displayed" % BENTO_SCRIPT)
            return

    mods = set_main(top_node, build_node)
    if mods:
        mods[0].startup(global_context)
    for command in find_hook_commands(mods):
        global_context.register_command(command.name, command)
    register_stuff(global_context)
    _big_ugly_hack()
    if mods:
        mods[0].options(global_context)

    # FIXME: this registered options for new commands registered in hook. It
    # should be made all in one place (hook and non-hook)
    for cmd_name in global_context.command_names(public_only=False):
        if not OPTIONS_REGISTRY.is_registered(cmd_name):
            register_options(global_context, cmd_name)

    for cmd_name in global_context.command_names():
        for hook in find_pre_hooks(mods, cmd_name):
            global_context.add_pre_hook(hook, cmd_name)
        for hook in find_post_hooks(mods, cmd_name):
            global_context.add_post_hook(hook, cmd_name)

    try:
        return _main(global_context, popts, run_node, top_node, build_node)
    finally:
        if mods:
            mods[0].shutdown()

def parse_global_options(argv):
    context = OptionsContext(usage="%prog [options] [cmd_name [cmd_options]]")
    context.add_option(Option("--version", "-v", dest="show_version", action="store_true",
                              help="Version"))
    context.add_option(Option("--full-version", dest="show_full_version", action="store_true",
                              help="Full version"))
    context.add_option(Option("--build-directory", dest="build_directory",
                              help="Build directory as relative path from cwd (default: '%default')"))
    context.add_option(Option("--bento-info", dest="bento_info",
                              help="Bento location as a relative path from cwd (default: '%default'). " \
                                   "The base name (without its component) must be 'bento.info("))
    context.add_option(Option("-h", "--help", dest="show_help", action="store_true",
                              help="Display help and exit"))
    context.parser.set_defaults(show_version=False, show_full_version=False, show_help=False,
                                build_directory="build", bento_info="bento.info")
    OPTIONS_REGISTRY.register("", context)

    global_args, cmd_args = [], []
    for i, a in enumerate(argv):
        if a.startswith("-"):
            global_args.append(a)
        else:
            cmd_args = argv[i:]
            break

    ret = {"cmd_name": None, "cmd_opts": None}
    if cmd_args:
        ret["cmd_name"] = cmd_args[0]
        ret["cmd_opts"] = cmd_args[1:]

    o, a = context.parser.parse_args(global_args)
    ret["show_usage"] = o.show_help
    ret["build_directory"] = o.build_directory
    if not os.path.basename(o.bento_info) == BENTO_SCRIPT:
        context.parser.error("Invalid value for --bento-info: %r (basename should be %r)" % \
                             (o.bento_info, BENTO_SCRIPT))

    ret["bento_info"] = o.bento_info
    ret["show_version"] = o.show_version
    ret["show_full_version"] = o.show_full_version

    return ret

def _main(global_context, popts, run_node, top_node, build_node):
    if popts["show_version"]:
        print(bento.__version__)
        return 0

    if popts["show_full_version"]:
        print(bento.__version__ + "git" + bento.__git_revision__)
        return 0

    if popts["show_usage"]:
        ctx_klass = global_context.retrieve_context("help")
        cmd = global_context.retrieve_command('help')
        cmd.run(ctx_klass(global_context, [], OPTIONS_REGISTRY.retrieve('help'), None, None))
        return 0

    cmd_name = popts["cmd_name"]
    cmd_opts = popts["cmd_opts"]

    if not cmd_name:
        print("Type '%s help' for usage." % SCRIPT_NAME)
        return 1
    else:
        if not global_context.is_command_registered(cmd_name):
            raise UsageException("%s: Error: unknown command %r" % (SCRIPT_NAME, cmd_name))
        else:
            run_cmd(global_context, cmd_name, cmd_opts, run_node, top_node, build_node)

def _get_package_with_user_flags(cmd_name, cmd_argv, package_options, top_node, build_node):
    from bento.commands.configure import _get_flag_values

    cmd_data_db = build_node.make_node(CMD_DATA_DUMP)
    configure_argv = _get_cmd_data_provider(cmd_data_db).get_argv("configure")

    p = OPTIONS_REGISTRY.retrieve("configure")
    o, a = p.parser.parse_args(configure_argv)
    flag_values = _get_flag_values(package_options.flag_options.keys(), o)

    bento_info = top_node.find_node(BENTO_SCRIPT)
    return _get_cached_package().get_package(bento_info, flag_values)

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

def run_dependencies(global_context, cmd_name, run_node, top_node, build_node,
        pkg, package_options):
    cmd_data_db = build_node.make_node(CMD_DATA_DUMP)

    deps = CMD_SCHEDULER.order(cmd_name)
    for cmd_name in deps:
        cmd = global_context.retrieve_command(cmd_name)
        cmd_argv = _get_cmd_data_provider(cmd_data_db).get_argv(cmd_name)
        ctx_klass = CONTEXT_REGISTRY.retrieve(cmd_name)
        run_cmd_in_context(global_context, cmd, cmd_name, cmd_argv, ctx_klass,
                run_node, top_node, pkg, package_options)

def is_help_only(cmd_name, cmd_argv):
    p = OPTIONS_REGISTRY.retrieve(cmd_name)
    o, a = p.parser.parse_args(cmd_argv)
    return o.help is True

def run_cmd(global_ctx, cmd_name, cmd_opts, run_node, top_node, build_node):
    cmd = global_ctx.retrieve_command(cmd_name)

    # XXX: fix this special casing (commands which do not need a pkg instance)
    if cmd_name in ["help", "convert"]:
        options_ctx = OPTIONS_REGISTRY.retrieve(cmd_name)
        ctx_klass = CONTEXT_REGISTRY.retrieve(cmd_name)
        ctx = ctx_klass(global_ctx, cmd_opts, options_ctx, PackageDescription(), run_node)
        # XXX: hack for help command to get option context for any command
        # without making help depends on bentomakerlib
        ctx.options_registry = OPTIONS_REGISTRY
        cmd.run(ctx)
        return

    bento_info = top_node.find_node(BENTO_SCRIPT)
    if bento_info is None:
        raise UsageException("Error: no %s found !" % os.path.join(top_node.abspath(), BENTO_SCRIPT))

    package_options = __get_package_options(top_node)
    pkg = _get_package_with_user_flags(cmd_name, cmd_opts, package_options, top_node, build_node)
    if is_help_only(cmd_name, cmd_opts):
        options_context = OPTIONS_REGISTRY.retrieve(cmd_name)
        p = options_context.parser
        o, a = p.parse_args(cmd_opts)
        if o.help:
            p.print_help()
    else:
        run_dependencies(global_ctx, cmd_name, run_node, top_node, build_node,
                pkg, package_options)

        ctx_klass = CONTEXT_REGISTRY.retrieve(cmd_name)
        run_cmd_in_context(global_ctx, cmd, cmd_name, cmd_opts, ctx_klass,
                run_node, top_node, pkg, package_options)

        cmd_data_db = build_node.make_node(CMD_DATA_DUMP)
        _set_cmd_data_provider(cmd_name, cmd_opts, cmd_data_db)

def noexc_main(argv=None):
    def _print_debug():
        if BENTOMAKER_DEBUG:
            tb = sys.exc_info()[2]
            traceback.print_tb(tb)
    def _print_error(msg):
        pprint('RED', msg)
        pprint('RED', "(You can see the traceback by setting the " \
                      "BENTOMAKER_DEBUG=1 environment variable)")

    try:
        ret = main(argv)
    except UsageException:
        _print_debug()
        e = extract_exception()
        _print_error(str(e))
        sys.exit(1)
    except ParseError:
        _print_debug()
        e = extract_exception()
        _print_error(str(e))
        sys.exit(2)
    except ConvertionError:
        _print_debug()
        e = extract_exception()
        _print_error("".join(e.args))
        sys.exit(3)
    except CommandExecutionFailure:
        _print_debug()
        e = extract_exception()
        _print_error("".join(e.args))
        sys.exit(4)
    except bento.core.errors.ConfigurationError:
        _print_debug()
        e = extract_exception()
        _print_error(e)
        sys.exit(8)
    except bento.core.errors.BuildError:
        _print_debug()
        e = extract_exception()
        _print_error(e)
        sys.exit(16)
    except bento.core.errors.InvalidPackage:
        _print_debug()
        e = extract_exception()
        _print_error(e)
        sys.exit(32)
    except Exception:
        msg = """\
%s: Error: %s crashed (uncaught exception %s: %s).
Please report this on bento issue tracker:
    http://github.com/cournape/bento/issues"""
        if not BENTOMAKER_DEBUG:
            msg += "\nYou can get a full traceback by setting BENTOMAKER_DEBUG=1"
        else:
            _print_debug()
        e = extract_exception()
        pprint('RED',  msg % (SCRIPT_NAME, SCRIPT_NAME, e.__class__, str(e)))
        sys.exit(1)
    sys.exit(ret)

if __name__ == '__main__':
    noexc_main()
