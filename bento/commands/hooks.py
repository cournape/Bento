from bento.commands.core \
    import \
        register_command

__HOOK_REGISTRY = {}
__PRE_HOOK_REGISTRY = {}
__POST_HOOK_REGISTRY = {}
__COMMANDS_OVERRIDE = {}

def add_to_registry(func, category):
    global __HOOK_REGISTRY

    if not category in __HOOK_REGISTRY:
        __HOOK_REGISTRY[category] = [func]
    else:
        __HOOK_REGISTRY[category].append(func)

def override_command(command, func):
    global __COMMANDS_OVERRIDE

    __COMMANDS_OVERRIDE[command] = (func,)

def add_to_pre_registry(func, cmd_name):
    global __PRE_HOOK_REGISTRY

    if not cmd_name in __PRE_HOOK_REGISTRY:
        __PRE_HOOK_REGISTRY[cmd_name] = [func]
    else:
        __PRE_HOOK_REGISTRY[cmd_name].append(func)

def add_to_post_registry(func, cmd_name):
    global __POST_HOOK_REGISTRY

    if not cmd_name in __POST_HOOK_REGISTRY:
        __POST_HOOK_REGISTRY[cmd_name] = [func]
    else:
        __POST_HOOK_REGISTRY[cmd_name].append(func)

def get_registry_categories():
    global __HOOK_REGISTRY

    return __HOOK_REGISTRY.keys()

def get_registry_category(categorie):
    global __HOOK_REGISTRY

    return __HOOK_REGISTRY[categorie]

def get_pre_hooks(cmd_name):
    global __PRE_HOOK_REGISTRY
    return __PRE_HOOK_REGISTRY.get(cmd_name, None)

def get_post_hooks(cmd_name):
    global __POST_HOOK_REGISTRY
    return __POST_HOOK_REGISTRY.get(cmd_name, None)

def get_command_override(cmd_name):
    global __COMMANDS_OVERRIDE
    return __COMMANDS_OVERRIDE.get(cmd_name, None)

def pre_build(f):
    add_to_registry((f,), "pre_build")
    add_to_pre_registry((f,), "build")

def post_configure(f):
    add_to_registry((f,), "post_configure")
    add_to_post_registry((f,), "configure")

def pre_configure(f):
    add_to_registry((f,), "pre_configure")
    add_to_pre_registry((f,), "configure")

def post_sdist(f):
    add_to_registry((f,), "post_sdist")
    add_to_post_registry((f,), "sdist")

def pre_sdist(f):
    add_to_registry((f,), "pre_sdist")
    add_to_pre_registry((f,), "sdist")

def override(f):
    override_command(f.__name__, f)

def command_register(f, *a, **kw):
    ret = f(*a, **kw)
    for cmd_name, cmd_class in ret.items():
        register_command(cmd_name, cmd_class)
