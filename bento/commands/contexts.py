from bento.commands.configure \
    import \
        _compute_scheme, set_scheme_options
from bento.commands.registries \
    import \
        CommandRegistry, ContextRegistry, OptionsRegistry
from bento.commands.dependency \
    import \
        CommandScheduler
from bento.commands.hooks \
    import \
        HookRegistry
from bento.commands.wrapper_utils \
    import \
        resolve_and_run_command
from bento.utils.utils \
    import \
        read_or_create_dict

from six.moves \
    import \
        cPickle

class GlobalContext(object):
    def __init__(self, command_data_db, commands_registry=None, contexts_registry=None,
            options_registry=None, commands_scheduler=None):
        self._commands_registry = commands_registry or CommandRegistry()
        self._contexts_registry = contexts_registry or ContextRegistry()
        self._options_registry = options_registry or OptionsRegistry()
        self._scheduler = commands_scheduler or CommandScheduler()
        self._hooks_registry = HookRegistry()

        self.backend = None
        self._package_options = None

        self._command_data_db = command_data_db
        if command_data_db is None:
            self._command_data_store = {}
        else:
            self._command_data_store = read_or_create_dict(command_data_db.abspath())

    def store(self):
        if self._command_data_db:
            self._command_data_db.safe_write(cPickle.dumps(self._command_data_store), "wb")

    def run_command(self, command_name, command_argv, package, run_node):
        resolve_and_run_command(self, command_name, command_argv, run_node, package)

    #------------
    # Command API
    #------------
    def register_command(self, cmd_name, cmd, public=True):
        """Register a command name to a command instance.

        Parameters
        ----------
        cmd_name: str
            name of the command
        cmd: object
            instance from a subclass of Command
        """
        self._commands_registry.register(cmd_name, cmd, public)

    def retrieve_command(self, cmd_name):
        """Return the command instance registered for the given command name."""
        return self._commands_registry.retrieve(cmd_name)

    def is_command_registered(self, cmd_name):
        """Return True if the command is registered."""
        return self._commands_registry.is_registered(cmd_name)

    def command_names(self, public_only=True):
        if public_only:
            return self._commands_registry.public_command_names()
        else:
            return self._commands_registry.command_names()

    #--------------------
    # Command Context API
    #--------------------
    def register_command_context(self, cmd_name, klass):
        self._contexts_registry.register(cmd_name, klass)

    def retrieve_command_context(self, cmd_name):
        return self._contexts_registry.retrieve(cmd_name)

    def is_command_context_registered(self, cmd_name):
        """Return True if the command context is registered."""
        return self._contexts_registry.is_registered(cmd_name)

    #--------------------
    # Command Options API
    #--------------------
    def register_options_context_without_command(self, name, context):
        """Register options_context for special 'commands' that has no command
        context attached to them

        This is typically used for global help, and other help-only commands
        such as 'globals'."""
        return self._options_registry.register(name, context)

    def register_options_context(self, cmd_name, context):
        cmd = self.retrieve_command(cmd_name)
        if self._package_options is not None and hasattr(cmd, "register_options"):
            cmd.register_options(context, self._package_options)

        return self._options_registry.register(cmd_name, context)

    def retrieve_options_context(self, cmd_name):
        return self._options_registry.retrieve(cmd_name)

    def is_options_context_registered(self, cmd_name):
        return self._options_registry.is_registered(cmd_name)

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
        ctx = self._options_registry.retrieve(cmd_name)
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
        ctx = self._options_registry.retrieve(cmd_name)
        ctx.add_option(option, group)

    def register_package_options(self, package_options):
        self._package_options = package_options

    # FIXME: rename
    def retrieve_scheme(self):
        """Return the path scheme, including any custom path defined in the
        bento.info script (Path sections)."""
        return _compute_scheme(self._package_options)

    def retrieve_configured_scheme(self, command_argv=None):
        """Return the configured path scheme with the given command argv.

        Note
        ----
        This can only be safely called once regiser_options_context has been
        called for the configure command"""
        assert self._package_options is not None
        assert self.is_options_context_registered("configure")

        if command_argv is None:
            command_argv = []
        scheme = _compute_scheme(self._package_options)
        options_context = self.retrieve_options_context("configure")
        o, a = options_context.parser.parse_args(command_argv)
        set_scheme_options(scheme, o, self._package_options)
        return scheme

    #-----------------------
    # Command dependency API
    #-----------------------
    def set_before(self, cmd_name, cmd_name_before):
        """Specify that command cmd_name_before should run before cmd_name."""
        self._scheduler.set_before(cmd_name, cmd_name_before)

    def set_after(self, cmd_name, cmd_name_after):
        """Specify that command cmd_name_before should run after cmd_name."""
        self._scheduler.set_after(cmd_name, cmd_name_after)

    def retrieve_dependencies(self, cmd_name):
        """Return the ordered list of command names to run before the given
        command name."""
        return self._scheduler.order(cmd_name)

    #---------
    # Hook API
    #---------
    def add_pre_hook(self, hook, cmd_name):
        self._hooks_registry.add_pre_hook(hook, cmd_name)

    def add_post_hook(self, hook, cmd_name):
        self._hooks_registry.add_post_hook(hook, cmd_name)

    def retrieve_pre_hooks(self, cmd_name):
        return self._hooks_registry.retrieve_pre_hooks(cmd_name)

    def retrieve_post_hooks(self, cmd_name):
        return self._hooks_registry.retrieve_post_hooks(cmd_name)

    #------------
    # Backend API
    #------------
    def register_backend(self, backend):
        self.backend = backend

    def retrieve_command_argv(self, command_name):
        # FIXME: returning empty list if nothing is available hides bugs.
        return self._command_data_store.get(command_name, [])

    def save_command_argv(self, command_name, command_argv):
        self._command_data_store[command_name] = command_argv
