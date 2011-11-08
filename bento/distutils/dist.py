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

from bento.commands.wrapper_utils \
    import \
        set_main
from bento.conv \
    import \
        pkg_to_distutils_meta
from bento.core.node \
    import \
        create_root_with_source_tree
from bento.core.package \
    import \
        PackageDescription
from bento.commands.context \
    import \
        GlobalContext, CONTEXT_REGISTRY
from bento.commands.cmd_contexts \
    import \
        CmdContext, SdistContext
from bento.commands.yaku_contexts \
    import \
        ConfigureYakuContext, BuildYakuContext

from bento.commands.dependency \
    import \
        CommandScheduler
from bento.commands.api \
    import \
        COMMANDS_REGISTRY, ConfigureCommand, BuildCommand, InstallCommand, SdistCommand
from bento.commands.options \
    import \
        OptionsRegistry, OptionsContext
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

def global_context_factory():
    # FIXME: factor this out with the similar code in bentomakerlib
    options_registry = OptionsRegistry()
    # This is a dummy for now, to fulfill global_context API
    cmd_scheduler = CommandScheduler()
    register_commands()
    register_command_contexts()
    for cmd_name in COMMANDS_REGISTRY.get_command_names():
        if not options_registry.is_registered(cmd_name):
            cmd_klass = COMMANDS_REGISTRY.get_command(cmd_name)
            options_context = OptionsContext.from_command(cmd_klass)
            options_registry.register_command(cmd_name, options_context)
    global_context = GlobalContext(COMMANDS_REGISTRY, CONTEXT_REGISTRY,
                                   options_registry, cmd_scheduler)
    return global_context

def register_command_contexts():
    CONTEXT_REGISTRY.set_default(CmdContext)
    if not CONTEXT_REGISTRY.is_registered("configure"):
        CONTEXT_REGISTRY.register("configure", ConfigureYakuContext)
    if not CONTEXT_REGISTRY.is_registered("build"):
        CONTEXT_REGISTRY.register("build", BuildYakuContext)
    if not CONTEXT_REGISTRY.is_registered("sdist"):
        CONTEXT_REGISTRY.register("sdist", SdistContext)

def register_commands():
    COMMANDS_REGISTRY.register_command("configure", ConfigureCommand)
    COMMANDS_REGISTRY.register_command("build", BuildCommand)
    COMMANDS_REGISTRY.register_command("install", InstallCommand)
    COMMANDS_REGISTRY.register_command("sdist", SdistCommand)

class BentoDistribution(Distribution):
    def get_command_class(self, command):
        # Better raising an error than having some weird behavior for a command
        # we don't support
        if not command in _BENTO_MONKEYED_CLASSES:
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

        self.global_context = global_context_factory()
        modules = set_main(self.top_node, self.build_node, self.pkg)

    def has_data_files(self):
        return len(self.pkg.data_files) > 0        

# Install it throughout the distutils
_MODULES = []
if _is_setuptools_activated():
    import setuptools.dist
    _MODULES.append(setuptools.dist)
import distutils.dist, distutils.core, distutils.cmd
_MODULES.extend([distutils.dist, distutils.core, distutils.cmd])
for module in _MODULES:
    module.Distribution = BentoDistribution
