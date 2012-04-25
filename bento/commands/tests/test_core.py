import os

from bento.compat.api.moves \
    import \
        unittest
from bento.core \
    import \
        PackageDescription
from bento.core.node \
    import \
        create_first_node
from bento.commands.core \
    import \
        HelpCommand, Command
from bento.commands.command_contexts \
    import \
        HelpContext
from bento.commands.wrapper_utils \
    import \
        run_command_in_context
from bento.commands.contexts \
    import \
        GlobalContext
from bento.commands.options \
    import \
        OptionsContext
import bento.commands.registries

class TestHelpCommand(unittest.TestCase):
    def setUp(self):
        self.run_node = create_first_node(os.getcwd())

        registry = bento.commands.registries.CommandRegistry()

        # help command assumes those always exist
        registry.register("configure", Command)
        registry.register("build", Command)
        registry.register("install", Command)
        registry.register("sdist", Command)
        registry.register("build_wininst", Command)
        registry.register("build_egg", Command)
        self.registry = registry

        self.options_registry = bento.commands.registries.OptionsRegistry()
        self.options_registry.register("configure", OptionsContext())

    def test_simple(self):
        help = HelpCommand()
        options = OptionsContext()
        for option in HelpCommand.common_options:
            options.add_option(option)
        global_context = GlobalContext(None,
                commands_registry=self.registry,
                options_registry=self.options_registry)
        pkg = PackageDescription()
        context = HelpContext(global_context, [], options, pkg, self.run_node)

        run_command_in_context(context, help)

    def test_command(self):
        help = HelpCommand()
        options = OptionsContext()
        for option in HelpCommand.common_options:
            options.add_option(option)
        pkg = PackageDescription()

        global_context = GlobalContext(None,
                commands_registry=self.registry,
                options_registry=self.options_registry)
        context = HelpContext(global_context, ["configure"], options, pkg, self.run_node)

        run_command_in_context(context, help)
