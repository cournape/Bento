#! /usr/bin/env python
#import demandimport
#demandimport.enable()
import sys
import os
import traceback
import warnings

import bento

from bento.utils.utils \
    import \
        pprint, extract_exception
from bento._config \
    import \
        BENTO_SCRIPT, DB_FILE, _SUB_BUILD_DIR
from bento.core \
    import \
        PackageDescription
from bento.compat.api \
    import \
        defaultdict, input
import bento.core.node

from bento.commands.build \
    import \
        BuildCommand
from bento.commands.build_egg \
    import \
        BuildEggCommand
from bento.commands.build_pkg_info \
    import \
        BuildPkgInfoCommand
from bento.commands.build_wininst \
    import \
        BuildWininstCommand
from bento.commands.configure \
    import \
        ConfigureCommand
from bento.commands.core \
    import \
        HelpCommand
from bento.commands.dependency \
    import \
        CommandScheduler
from bento.commands.hooks \
    import \
        find_pre_hooks, find_post_hooks, find_startup_hooks, \
        find_shutdown_hooks, find_options_hooks, find_command_hooks
from bento.commands.install \
    import \
        InstallCommand
from bento.commands.parse \
    import \
        ParseCommand
from bento.commands.register \
    import \
        RegisterPyPI
from bento.commands.registries \
    import \
        CommandRegistry, ContextRegistry, OptionsRegistry
from bento.commands.sdist \
    import \
        SdistCommand
from bento.commands.sphinx_command \
    import \
        SphinxCommand
from bento.commands.upload \
    import \
        UploadPyPI
from bento.commands.options \
    import \
        OptionsContext, Option

from bento.backends.utils \
    import \
        load_backend
from bento.backends.yaku_backend \
    import \
        BuildYakuContext, ConfigureYakuContext
from bento.commands.command_contexts \
    import \
        HelpContext, SdistContext, ContextWithBuildDirectory
from bento.commands.wrapper_utils \
    import \
        set_main, run_with_dependencies
from bento.commands.contexts \
    import \
        GlobalContext
from bento.convert \
    import \
        ConvertCommand, DetectTypeCommand
import bento.errors
import bento.warnings

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

# Path relative to build directory
CMD_DATA_DUMP = os.path.join(_SUB_BUILD_DIR, "cmd_data.db")

class GlobalOptions(object):
    def __init__(self, cmd_name, cmd_argv, show_usage, build_directory,
            bento_info, show_version, show_full_version, disable_autoconfigure):
        self.cmd_name = cmd_name
        self.cmd_argv = cmd_argv
        self.show_usage = show_usage
        self.build_directory = build_directory
        self.bento_info = bento_info
        self.show_version = show_version
        self.show_full_version = show_full_version
        self.disable_autoconfigure = disable_autoconfigure

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
    global_context.register_command("sphinx", SphinxCommand())
    global_context.register_command("register_pypi", RegisterPyPI())
    global_context.register_command("upload_pypi", UploadPyPI())

    global_context.register_command("build_pkg_info", BuildPkgInfoCommand(), public=False)
    global_context.register_command("parse", ParseCommand(), public=False)
    global_context.register_command("detect_type", DetectTypeCommand(), public=False)
 
    if sys.platform == "darwin":
        import bento.commands.build_mpkg
        global_context.register_command("build_mpkg",
            bento.commands.build_mpkg.BuildMpkgCommand(), public=False)
        global_context.set_before("build_mpkg", "build")

    if sys.platform == "win32":
        from bento.commands.build_msi \
            import \
                BuildMsiCommand
        global_context.register_command("build_msi", BuildMsiCommand())
        global_context.set_before("build_msi", "build")

def register_options(global_context, cmd_name):
    """Register options for the given command."""
    cmd = global_context.retrieve_command(cmd_name)
    context = OptionsContext.from_command(cmd)

    if not global_context.is_options_context_registered(cmd_name):
        global_context.register_options_context(cmd_name, context)

def register_options_special(global_context):
    # Register options for special topics not attached to a "real" command
    # (e.g. 'commands')
    context = OptionsContext()
    def print_usage():
        print(get_usage(global_context))
    context.parser.print_help = print_usage
    global_context.register_options_context_without_command("commands", context)

    context = OptionsContext()
    def print_help():
        global_options = global_context.retrieve_options_context("")
        p = global_options.parser
        return(p.print_help())
    context.parser.print_help = print_help
    global_context.register_options_context_without_command("globals", context)

def register_command_contexts(global_context):
   # global_context.register_default_context(CmdContext)
    default_mapping = defaultdict(lambda: ContextWithBuildDirectory)
    default_mapping.update(dict([
            ("configure", ConfigureYakuContext),
            ("build", BuildYakuContext),
            ("build_egg", ContextWithBuildDirectory),
            ("build_wininst", ContextWithBuildDirectory),
            ("build_mpkg", ContextWithBuildDirectory),
            ("install", ContextWithBuildDirectory),
            ("sdist", SdistContext),
            ("help", HelpContext)]))

    for cmd_name in global_context.command_names(public_only=False):
        if not global_context.is_command_context_registered(cmd_name):
            global_context.register_command_context(cmd_name, default_mapping[cmd_name])

# All the global state/registration stuff goes here
def register_stuff(global_context):
    register_commands(global_context)
    register_options_special(global_context)
    register_command_contexts(global_context)

def main(argv=None):
    if hasattr(os, "getuid"):
        if os.getuid() == 0:
            pprint("RED", "Using bentomaker under root/sudo is *strongly* discouraged - do you want to continue ? y/N")
            ans = input()
            if not ans.lower() in ["y", "yes"]:
                raise bento.errors.UsageException("bentomaker execution canceld (not using bentomaker with admin privileges)")

    if argv is None:
        argv = sys.argv[1:]

    options_context = create_global_options_context()
    popts = parse_global_options(options_context, argv)

    cmd_name = popts.cmd_name

    if popts.show_version:
        print(bento.__version__)
        return

    if popts.show_full_version:
        print(bento.__version__ + "git" + bento.__git_revision__)
        return

    source_root = os.path.join(os.getcwd(), os.path.dirname(popts.bento_info))
    build_root = os.path.join(os.getcwd(), popts.build_directory)

    top_node, build_node, run_node = bento.core.node.create_base_nodes(source_root, build_root)
    if run_node != top_node and run_node.is_src():
        raise bento.errors.UsageException("You cannot execute bentomaker in a subdirectory of the source tree !")
    if run_node != build_node and run_node.is_bld():
        raise bento.errors.UsageException("You cannot execute bentomaker in a subdirectory of the build tree !")

    global_context = GlobalContext(build_node.make_node(CMD_DATA_DUMP),
                                   CommandRegistry(), ContextRegistry(),
                                   OptionsRegistry(), CommandScheduler())
    global_context.register_options_context_without_command("", options_context)

    if not popts.disable_autoconfigure:
        global_context.set_before("build", "configure")
    global_context.set_before("build_egg", "build")
    global_context.set_before("build_wininst", "build")
    global_context.set_before("install", "build")

    if cmd_name and cmd_name not in ["convert"]:
        return _wrapped_main(global_context, popts, run_node, top_node, build_node)
    else:
        # XXX: is cached package necessary here ?
        cached_package = None
        register_stuff(global_context)
        for cmd_name in global_context.command_names():
            register_options(global_context, cmd_name)
        return _main(global_context, cached_package, popts, run_node, top_node, build_node)

def _wrapped_main(global_context, popts, run_node, top_node, build_node):
    # Some commands work without a bento description file (convert, help)
    # FIXME: this should not be called here then - clearly separate commands
    # which require bento.info from the ones who do not
    bento_info_node = top_node.find_node(BENTO_SCRIPT)
    if bento_info_node is not None:
        db_node = build_node.make_node(DB_FILE)
        cached_package = CachedPackage(db_node)
        package = cached_package.get_package(bento_info_node)
        package_options = cached_package.get_options(bento_info_node)

        if package.use_backends:
            if len(package.use_backends) > 1:
                raise ValueError("Only up to one backend supported for now")
            else:
                assert global_context.backend is None
                global_context.backend = load_backend(package.use_backends[0])()
        global_context.register_package_options(package_options)

        mods = set_main(package, top_node, build_node)

    else:
        warnings.warn("No %r file in current directory - only generic options "
                      "will be displayed" % BENTO_SCRIPT, bento.warnings.NoBentoInfoWarning)
        cached_package = None
        package_options = None
        mods = []

    startup_hooks = find_startup_hooks(mods)
    option_hooks = find_options_hooks(mods)
    shutdown_hooks = find_shutdown_hooks(mods)

    if startup_hooks:
        # FIXME: there should be an error or a warning if startup defined in
        # mods beyond the first one
        startup_hooks[0](global_context)

    if global_context.backend:
        global_context.backend.register_command_contexts(global_context)
    for command in find_command_hooks(mods):
        global_context.register_command(command.name, command)
    register_stuff(global_context)
    for cmd_name in global_context.command_names():
        register_options(global_context, cmd_name)

    if global_context.backend:
        global_context.backend.register_options_contexts(global_context)
    if option_hooks:
        # FIXME: there should be an error or a warning if shutdown defined in
        # mods beyond the first one
        option_hooks[0](global_context)

    # FIXME: this registered options for new commands registered in hook. It
    # should be made all in one place (hook and non-hook)
    for cmd_name in global_context.command_names(public_only=False):
        if not global_context.is_options_context_registered(cmd_name):
            register_options(global_context, cmd_name)

    for cmd_name in global_context.command_names():
        for hook in find_pre_hooks(mods, cmd_name):
            global_context.add_pre_hook(hook, cmd_name)
        for hook in find_post_hooks(mods, cmd_name):
            global_context.add_post_hook(hook, cmd_name)

    try:
        return _main(global_context, cached_package, popts, run_node, top_node, build_node)
    finally:
        if shutdown_hooks:
            shutdown_hooks[0](global_context)

def create_global_options_context():
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
    context.add_option(Option("--disable-autoconfigure", dest="disable_autoconfigure",
                              action="store_true",
                              default=False,
                              help="""\
Do not automatically run configure before build. In this mode, the user is
expected to know what he is doing. This is mainly useful for developers, to
avoid running configure everytime (default: '%default')."""))
    context.add_option(Option("-h", "--help", dest="show_help", action="store_true",
                              help="Display help and exit"))
    context.parser.set_defaults(show_version=False, show_full_version=False, show_help=False,
                                build_directory="build", bento_info="bento.info")
    return context

def parse_global_options(context, argv):
    global_args, cmd_args = [], []
    for i, a in enumerate(argv):
        if a.startswith("-"):
            global_args.append(a)
        else:
            cmd_args = argv[i:]
            break

    cmd_name = None
    cmd_argv = None
    if cmd_args:
        cmd_name = cmd_args[0]
        cmd_argv = cmd_args[1:]

    o, a = context.parser.parse_args(global_args)
    show_usage = o.show_help
    build_directory = o.build_directory
    if not os.path.basename(o.bento_info) == BENTO_SCRIPT:
        context.parser.error("Invalid value for --bento-info: %r (basename should be %r)" % \
                             (o.bento_info, BENTO_SCRIPT))

    bento_info = o.bento_info
    show_version = o.show_version
    show_full_version = o.show_full_version

    global_options = GlobalOptions(cmd_name, cmd_argv, show_usage,
            build_directory, bento_info, show_version, show_full_version,
            o.disable_autoconfigure)
    return global_options

def _main(global_context, cached_package, popts, run_node, top_node, build_node):
    if popts.show_usage:
        context_klass = global_context.retrieve_command_context("help")
        cmd = global_context.retrieve_command('help')
        cmd.run(context_klass(global_context, [], global_context.retrieve_options_context('help'), None, None))
        return

    cmd_name = popts.cmd_name
    cmd_argv = popts.cmd_argv

    if not cmd_name:
        print("Type '%s help' for usage." % SCRIPT_NAME)
        return 1
    else:
        if not global_context.is_command_registered(cmd_name):
            raise bento.errors.UsageException("%s: Error: unknown command %r" % (SCRIPT_NAME, cmd_name))
        else:
            run_cmd(global_context, cached_package, cmd_name, cmd_argv, run_node, top_node, build_node)

def _get_package_user_flags(global_context, package_options, configure_argv):
    from bento.commands.configure import _get_flag_values

    p = global_context.retrieve_options_context("configure")
    o, a = p.parser.parse_args(configure_argv)
    flag_values = _get_flag_values(package_options.flag_options.keys(), o)

    return flag_values

def is_help_only(global_context, cmd_name, cmd_argv):
    p = global_context.retrieve_options_context(cmd_name)
    o, a = p.parser.parse_args(cmd_argv)
    return o.help is True

def get_running_package(global_context, cached_package, bento_info):
    """Return a PackageDescription instance after evaluation of the flags set
    up at configure time.

    Example
    -------
    For this bento.info::

        Name: foo

        Flag: bundle
            Description: foo
            Default: true

        Library:
            if flag(bundle):
                Packages: yeah

    if bentomaker was run as follows::

        bentomaker configure

    get_running_package will return a PackageDescription instance with
    package.packages set to ["yeah"], and if bentomaker was run as follows::

        bentomaker configure --bundle=false

    get_running_package will return a PackageDescription instance with
    package.packages set to [].
    """
    package_options = cached_package.get_options(bento_info)
    configure_argv = global_context.retrieve_command_argv("configure")
    flag_values = _get_package_user_flags(global_context, package_options, configure_argv)
    return cached_package.get_package(bento_info, flag_values)

def run_cmd(global_context, cached_package, cmd_name, cmd_argv, run_node, top_node, build_node):
    # XXX: fix this special casing (commands which do not need a pkg instance)
    if cmd_name in ["help", "convert"]:
        global_context.run_command(cmd_name, cmd_argv, PackageDescription(), run_node)
        return

    if is_help_only(global_context, cmd_name, cmd_argv):
        options_context = global_context.retrieve_options_context(cmd_name)
        options_context.parser.print_help()
        return

    bento_info = top_node.find_node(BENTO_SCRIPT)
    if bento_info is None:
        raise bento.errors.UsageException("Error: no %s found !" % os.path.join(top_node.abspath(), BENTO_SCRIPT))

    running_package = get_running_package(global_context, cached_package, bento_info)
    run_with_dependencies(global_context, cmd_name, cmd_argv, run_node, top_node, running_package)

    global_context.save_command_argv(cmd_name, cmd_argv)
    global_context.store()

def noexc_main(argv=None):
    def _print_debug():
        if BENTOMAKER_DEBUG:
            tb = sys.exc_info()[2]
            traceback.print_tb(tb)
    def _print_error(msg):
        pprint('RED', msg)
        if not BENTOMAKER_DEBUG:
            pprint('RED', "(You can see the traceback by setting the " \
                          "BENTOMAKER_DEBUG=1 environment variable)")

    try:
        main(argv)
    except bento.errors.BentoError:
        _print_debug()
        e = extract_exception()
        _print_error(str(e))
        sys.exit(2)
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

if __name__ == '__main__':
    noexc_main()
