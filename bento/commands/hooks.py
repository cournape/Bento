import os
import sys
import re

from bento.compat \
    import \
        inspect as compat_inspect
from bento.commands.core \
    import \
        command

SAFE_MODULE_NAME = re.compile("[^a-zA-Z_]")

__HOOK_REGISTRY = {}
__PRE_HOOK_REGISTRY = {}
__POST_HOOK_REGISTRY = {}
__COMMANDS_OVERRIDE = {}
__INIT_FUNCS = {}

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
    return __PRE_HOOK_REGISTRY.get(cmd_name, [])

def get_post_hooks(cmd_name):
    global __POST_HOOK_REGISTRY
    return __POST_HOOK_REGISTRY.get(cmd_name, [])

def get_command_override(cmd_name):
    global __COMMANDS_OVERRIDE
    return __COMMANDS_OVERRIDE.get(cmd_name, [])

def _make_hook_decorator(command_name, kind):
    name = "%s_%s" % (kind, command_name)
    help_bypass = False
    def decorator(f):
        local_dir = os.path.dirname(compat_inspect.stack()[1][1])
        add_to_registry((f, local_dir, help_bypass), name)
        if kind == "post":
            add_to_post_registry((f, local_dir, help_bypass), command_name)
        elif kind == "pre":
            add_to_pre_registry((f, local_dir, help_bypass), command_name)
        else:
            raise ValueError("invalid hook kind %s" % kind)
        return f
    return decorator

post_configure = _make_hook_decorator("configure", "post")
pre_configure = _make_hook_decorator("configure", "pre")
post_build = _make_hook_decorator("build", "post")
pre_build = _make_hook_decorator("build", "pre")
post_sdist = _make_hook_decorator("sdist", "post")
pre_sdist = _make_hook_decorator("sdist", "pre")

def override(f):
    override_command(f.__name__, f)

def options(f):
    __INIT_FUNCS["options"] = f
    return lambda context: f(context)

def startup(f):
    __INIT_FUNCS["startup"] = f
    return lambda context: f(context)

def shutdown(f):
    __INIT_FUNCS["shutdown"] = f
    return lambda context: f(context)

def dummy_startup(ctx):
    pass

def dummy_options(ctx):
    pass

def dummy_shutdown():
    pass

def create_hook_module(target):
    import imp

    safe_name = SAFE_MODULE_NAME.sub("_", target, len(target))
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
    if not "startup" in __INIT_FUNCS:
        module.startup = dummy_startup
    if not "options" in __INIT_FUNCS:
        module.options = dummy_options
    if not "shutdown" in __INIT_FUNCS:
        module.shutdown = dummy_shutdown

    return module
