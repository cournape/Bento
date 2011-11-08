import os.path as op

import yaku.context

from bento.core.subpackage \
    import \
        get_extensions, get_compiled_libraries
from bento.commands.cmd_contexts \
    import \
        CmdContext, ConfigureContext, BuildContext, SdistContext
from bento.commands.yaku_contexts \
    import \
        ConfigureYakuContext, BuildYakuContext
from bento.commands.distutils_contexts \
    import \
        DistutilsBuildContext, DistutilsConfigureContext

class ContextRegistry(object):
    def __init__(self, default=None):
        self._contexts = {}
        self.set_default(default)

    def set_default(self, default):
        self._default = default

    def is_registered(self, cmd_name):
        return cmd_name in self._contexts

    def register(self, cmd_name, context):
        if cmd_name in self._contexts:
            raise ValueError("context for command %r already registered !" % cmd_name)
        else:
            self._contexts[cmd_name] = context

    def retrieve(self, cmd_name):
        context = self._contexts.get(cmd_name, None)
        if context is None:
            if self._default is None:
                raise ValueError("No context registered for command %r" % cmd_name)
            else:
                return self._default
        else:
            return context

class GlobalContext(object):
    def __init__(self, commands_registry, contexts_registry, options_registry, commands_scheduler):
        self._commands_registry = commands_registry
        self._contexts_registry = contexts_registry
        self._options_registry = options_registry
        self._scheduler = commands_scheduler

    def register_command(self, cmd_name, klass):
        self._commands_registry.register(cmd_name, klass)

    def retrieve_command(self, cmd_name):
        return self._commands_registry.retrieve(cmd_name)

    def register_context(self, cmd_name, klass):
        self._contexts_registry.register(cmd_name, klass)

    def retrieve_context(self, cmd_name):
        return self._contexts_registry.retrieve(cmd_name)

    def retrieve_options_context(self, cmd_name):
        return self._options_registry.retrieve(cmd_name)

    def add_option_group(self, cmd_name, name, title):
        """Add a new option group for the given command.
        
        Parameters
        ----------
        cmd_name: str
            name of the command
        name: str
            name of the group option
        title: str
            title of the group
        """
        ctx = self._options_registry.get_options(cmd_name)
        ctx.add_group(name, title)

    def add_option(self, cmd_name, option, group=None):
        """Add a new option for the given command.

        Parameters
        ----------
        cmd_name: str
            name of the command
        option: str
            name of the option
        group: str, None
            group to associated with
        """
        ctx = self._options_registry.get_options(cmd_name)
        ctx.add_option(option, group)

    def set_before(self, cmd_name, cmd_name_before):
        """Specify that command cmd_name_before should run before cmd_name."""
        self._scheduler.set_before(cmd_name, cmd_name_before)

    def set_after(self, cmd_name, cmd_name_after):
        """Specify that command cmd_name_before should run after cmd_name."""
        self._scheduler.set_after(cmd_name, cmd_name_after)

class HelpContext(CmdContext):
    pass

CONTEXT_REGISTRY = ContextRegistry()
