import os
import sys

from bento.compat \
    import \
        inspect as compat_inspect

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
    local_dir = os.path.dirname(compat_inspect.stack()[2][1])

    if __COMMANDS_OVERRIDE.has_key(command):
        __COMMANDS_OVERRIDE[command].append((func, local_dir))
    else:
        __COMMANDS_OVERRIDE[command] = [(func, local_dir)]

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
    local_dir = os.path.dirname(compat_inspect.stack()[1][1])
    add_to_registry((f, local_dir), "pre_build")
    add_to_pre_registry((f, local_dir), "build")

def post_build(f):
    local_dir = os.path.dirname(compat_inspect.stack()[1][1])
    add_to_registry((f, local_dir), "post_build")
    add_to_post_registry((f, local_dir), "build")

def post_configure(f):
    local_dir = os.path.dirname(compat_inspect.stack()[1][1])
    add_to_registry((f, local_dir), "post_configure")
    add_to_post_registry((f, local_dir), "configure")

def pre_configure(f):
    local_dir = os.path.dirname(compat_inspect.stack()[1][1])
    add_to_registry((f, local_dir), "pre_configure")
    add_to_pre_registry((f, local_dir), "configure")

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

def dummy_startup():
    pass

def dummy_shutdown():
    pass

def create_hook_module(target):
    import imp

    # FIXME: really make the name safe
    safe_name = target.replace("/", "_")
    module_name = "bento_hook_%s" % safe_name
    main_file = os.path.abspath(target)
    module = imp.new_module(module_name)
    module.__file__ = main_file
    code = open(main_file).read()

    sys.path.insert(0, os.path.dirname(main_file))
    try:
        exec(compile(code, main_file, 'exec'), module.__dict__)
        sys.modules[module_name] = module
    finally:
        sys.path.pop(0)

    module.root_path = main_file
    if not hasattr(module, "startup"):
        module.startup = dummy_startup
    if not hasattr(module, "shutdown"):
        module.shutdown = dummy_shutdown

    return module
