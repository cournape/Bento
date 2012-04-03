class CommandRegistry(object):
    def __init__(self):
        # command line name -> command class
        self._klasses = {}
        # command line name -> None for private commands
        self._privates = {}

    def register(self, name, cmd_klass, public=True):
        if name in self._klasses:
            raise ValueError("context for command %r already registered !" % name)
        else:
            self._klasses[name] = cmd_klass
            if not public:
                self._privates[name] = None

    def retrieve(self, name):
        cmd_klass = self._klasses.get(name, None)
        if cmd_klass is None:
            raise ValueError("No command class registered for name %r" % name)
        else:
            return cmd_klass

    def is_registered(self, name):
        return name in self._klasses

    def command_names(self):
        return self._klasses.keys()

    def public_command_names(self):
        return [k for k in self._klasses.keys() if not k in self._privates]

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

class OptionsRegistry(object):
    """Registry for command -> option context"""
    def __init__(self):
        # command line name -> context *instance*
        self._contexts = {}

    def register(self, cmd_name, options_context):
        if cmd_name in self._contexts:
            raise ValueError("options context for command %r already registered !" % cmd_name)
        else:
            self._contexts[cmd_name] = options_context

    def is_registered(self, cmd_name):
        return cmd_name in self._contexts

    def retrieve(self, cmd_name):
        options_context = self._contexts.get(cmd_name, None)
        if options_context is None:
            raise ValueError("No options context registered for cmd_name %r" % cmd_name)
        else:
            return options_context
