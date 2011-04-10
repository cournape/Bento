import unittest
import copy

from bento.commands.configure \
    import \
        ConfigureCommand
from bento.commands.build \
    import \
        BuildCommand
from bento.commands.install \
    import \
        InstallCommand
from bento.commands.sdist \
    import \
        SdistCommand
from bento.commands.core \
    import \
        HelpCommand, Command
from bento.commands.context \
    import \
        CmdContext
from bento.commands.options \
    import \
        OptionsContext
import bento.commands.core

class TestHelpCommand(unittest.TestCase):
    def setUp(self):
        self.old_registry = bento.commands.core.COMMANDS_REGISTRY
        registry = copy.deepcopy(bento.commands.core.COMMANDS_REGISTRY)

        # help command assumes those always exist
        registry.register_command("configure", Command)
        registry.register_command("build", Command)
        registry.register_command("install", Command)
        registry.register_command("sdist", Command)
        registry.register_command("build_wininst", Command)
        registry.register_command("build_egg", Command)

        bento.commands.core.COMMANDS_REGISTRY = registry

        self.options_registry = bento.commands.options.OptionsRegistry()
        self.options_registry.register_command("configure", OptionsContext())

    def tearDown(self):
        bento.commands.core.COMMANDS_REGISTRY = self.old_registry

    def test_simple(self):
        help = HelpCommand()
        options = OptionsContext()
        for option in HelpCommand.common_options:
            options.add_option(option)
        context = CmdContext([], options, None, None)

        help.run(context)

    def test_command(self):
        help = HelpCommand()
        options = OptionsContext()
        for option in HelpCommand.common_options:
            options.add_option(option)
        context = CmdContext(["configure"], options, None, None)
        context.options_registry = self.options_registry

        help.run(context)
