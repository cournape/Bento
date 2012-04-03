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
