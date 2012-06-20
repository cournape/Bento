import os

from bento.distutils.utils \
    import \
        _is_setuptools_activated
if _is_setuptools_activated():
    from setuptools \
        import \
            Distribution
else:
    from distutils.dist \
        import \
            Distribution

from bento.commands.configure \
    import \
        _setup_options_parser
from bento.commands.core \
    import \
        HelpCommand
from bento.commands.hooks \
    import \
        find_pre_hooks, find_post_hooks, find_startup_hooks, \
        find_shutdown_hooks, find_options_hooks, find_command_hooks
from bento.commands.wrapper_utils \
    import \
        set_main
from bento.compat.api \
    import \
        defaultdict
from bento.conv \
    import \
        pkg_to_distutils_meta
from bento.core.node \
    import \
        create_root_with_source_tree
from bento.core.package \
    import \
        PackageDescription
from bento.core.options \
    import \
        PackageOptions
from bento.commands.contexts \
    import \
        GlobalContext
from bento.commands.command_contexts \
    import \
        CmdContext, SdistContext, ContextWithBuildDirectory
from bento.commands.registries \
    import \
        CommandRegistry, ContextRegistry, OptionsRegistry
from bento.backends.yaku_backend \
    import \
        ConfigureYakuContext, BuildYakuContext
from bento.commands.build_egg \
    import \
        BuildEggCommand
import bento.commands.wrapper_utils

from bento.commands.dependency \
    import \
        CommandScheduler
from bento.commands.build \
    import \
        BuildCommand
from bento.commands.configure \
    import \
        ConfigureCommand
from bento.commands.install \
    import \
        InstallCommand
from bento.commands.sdist \
    import \
        SdistCommand
from bento.commands.options \
    import \
        OptionsContext
from bento.distutils.commands.config \
    import \
        config
from bento.distutils.commands.build \
    import \
        build
from bento.distutils.commands.install \
    import \
        install
from bento.distutils.commands.sdist \
    import \
        sdist

_BENTO_MONKEYED_CLASSES = {"build": build, "config": config, "install": install, "sdist": sdist}

if _is_setuptools_activated():
    from bento.distutils.commands.bdist_egg \
        import \
            bdist_egg
    from bento.distutils.commands.egg_info \
        import \
            egg_info
    _BENTO_MONKEYED_CLASSES["bdist_egg"] = bdist_egg
    _BENTO_MONKEYED_CLASSES["egg_info"] = egg_info

def _setup_cmd_classes(attrs):
    cmdclass = attrs.get("cmdclass", {})
    for klass in _BENTO_MONKEYED_CLASSES:
        if not klass in cmdclass:
            cmdclass[klass] = _BENTO_MONKEYED_CLASSES[klass]
    attrs["cmdclass"] = cmdclass
    return attrs

def global_context_factory(package_options):
    # FIXME: factor this out with the similar code in bentomakerlib
    global_context = GlobalContext(None)
    global_context.register_package_options(package_options)

    register_commands(global_context)
    register_command_contexts(global_context)
    for cmd_name in global_context.command_names():
        cmd = global_context.retrieve_command(cmd_name)
        options_context = OptionsContext.from_command(cmd)

        if not global_context.is_options_context_registered(cmd_name):
            global_context.register_options_context(cmd_name, options_context)

    return global_context

def register_command_contexts(global_context):
    default_mapping = defaultdict(lambda: ContextWithBuildDirectory)
    default_mapping.update(dict([
            ("configure", ConfigureYakuContext),
            ("build", BuildYakuContext),
            ("install", ContextWithBuildDirectory),
            ("sdist", SdistContext)]))

    for cmd_name in global_context.command_names(public_only=False):
        if not global_context.is_command_context_registered(cmd_name):
            global_context.register_command_context(cmd_name, default_mapping[cmd_name])

def register_commands(global_context):
    global_context.register_command("configure", ConfigureCommand())
    global_context.register_command("build", BuildCommand())
    global_context.register_command("install", InstallCommand())
    global_context.register_command("sdist", SdistCommand())
    global_context.register_command("build_egg", BuildEggCommand())

class BentoDistribution(Distribution):
    def get_command_class(self, command):
        # Better raising an error than having some weird behavior for a command
        # we don't support
        if self.script_args is not None \
           and command in self.script_args \
           and command not in _BENTO_MONKEYED_CLASSES:
            raise ValueError("Command %s is not supported by bento.distutils compat layer" % command)
        return Distribution.get_command_class(self, command)

    def __init__(self, attrs=None):
        if attrs is None:
            attrs = {}

        if not "bento_info" in attrs:
            bento_info = "bento.info"
        else:
            bento_info = attrs["bento.info"]
        self.pkg = PackageDescription.from_file(bento_info)
        package_options = PackageOptions.from_file(bento_info)

        attrs = _setup_cmd_classes(attrs)

        d = pkg_to_distutils_meta(self.pkg)
        attrs.update(d)

        Distribution.__init__(self, attrs)

        self.packages = self.pkg.packages
        self.py_modules = self.pkg.py_modules
        if hasattr(self, "entry_points"):
            if self.entry_points is None:
                self.entry_points = {}
            console_scripts = [e.full_representation() for e in self.pkg.executables.values()]
            if "console_scripts" in self.entry_points:
                self.entry_points["console_scripts"].extend(console_scripts)
            else:
                self.entry_points["console_scripts"] = console_scripts

        source_root = os.getcwd()
        build_root = os.path.join(source_root, "build")
        root = create_root_with_source_tree(source_root, build_root)
        self.top_node = root._ctx.srcnode
        self.build_node = root._ctx.bldnode
        self.run_node = root._ctx.srcnode

        self.global_context = global_context_factory(package_options)
        mods = set_main(self.pkg, self.top_node, self.build_node)
        self._setup_hooks(self.pkg, self.global_context, mods)

    def _setup_hooks(self, package, global_context, mods):
        if package.use_backends:
            if len(package.use_backends) > 1:
                raise ValueError("Only up to one backend supported for now")
            else:
                assert global_context.backend is None
                global_context.backend = load_backend(package.use_backends[0])()

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
                # FIXME: this should be supported in global context directly
                # (redundant with bentomakerlib)
                cmd = global_context.retrieve_command(cmd_name)
                context = OptionsContext.from_command(cmd)

                if not global_context.is_options_context_registered(cmd_name):
                    global_context.register_options_context(cmd_name, context)

        for cmd_name in global_context.command_names():
            for hook in find_pre_hooks(mods, cmd_name):
                global_context.add_pre_hook(hook, cmd_name)
            for hook in find_post_hooks(mods, cmd_name):
                global_context.add_post_hook(hook, cmd_name)

    def run_command_in_context(self, cmd_name, cmd_argv):
        return bento.commands.wrapper_utils.resolve_and_run_command(self.global_context,
            cmd_name, cmd_argv, self.run_node, self.pkg)

    def has_data_files(self):
        return len(self.pkg.data_files) > 0        
