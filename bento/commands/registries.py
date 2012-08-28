from bento.compat.api \
    import \
        defaultdict

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

class _Dummy(object):
    pass

class _RegistryBase(object):
    """A simple registry of sets of callbacks, one set per category."""
    def __init__(self):
        self._callbacks = {}
        self.categories = _Dummy()

    def register_category(self, category, default_builder):
        if category in self._callbacks:
            raise ValueError("Category %r already registered" % category)
        else:
            self._callbacks[category] = defaultdict(lambda: default_builder)
            setattr(self.categories, category, _Dummy())

    def register_callback(self, category, name, builder):
        c = self._callbacks.get(category, None)
        if c is not None:
            c[name] = builder
            cat = getattr(self.categories, category)
            setattr(cat, name, builder)
        else:
            raise ValueError("category %s is not registered yet" % category)

    def callback(self, category, name):
        if not category in self._callbacks:
            raise ValueError("Unregistered category %r" % category)
        else:
            return self._callbacks[category][name]

    def default_callback(self, category, *a, **kw):
        if not category in self._callbacks:
            raise ValueError("Unregistered category %r" % category)
        else:
            return self._callbacks[category].default_factory()(*a, **kw)

class BuilderRegistry(_RegistryBase):
    builder = _RegistryBase.callback

class ISectionRegistry(_RegistryBase):
    registrer = _RegistryBase.callback

class OutputRegistry(object):
    def __init__(self, categories=None):
        self.categories = {}
        self.installed_categories = {}
        if categories:
            for category, installed_category in categories:
                self.register_category(category, installed_category)

    def register_category(self, category, installed_category):
        if category in self.categories:
            raise ValueError("Category %r already registered")
        else:
            self.categories[category] = {}
            self.installed_categories[category] = installed_category

    def register_outputs(self, category, name, nodes, from_node, target_dir):
        if not category in self.categories:
            raise ValueError("Unknown category %r" % category)
        else:
            cat = self.categories[category]
            if name in cat:
                raise ValueError("Outputs for categoryr=%r and name=%r already registered" % (category, name))
            else:
                cat[name] = (nodes, from_node, target_dir)

    def iter_category(self, category):
        if not category in self.categories:
            raise ValueError("Unknown category %r" % category)
        else:
            for k, v in self.categories[category].items():
                yield k, v[0], v[1], v[2]

    def iter_over_category(self):
        for category in self.categories:
            for name, nodes, from_node, target_dir in self.iter_category(category):
                yield category, name, nodes, from_node, target_dir

