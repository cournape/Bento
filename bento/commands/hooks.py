import os
import sys

from bento.compat \
    import \
        inspect as compat_inspect
from bento.commands.core \
    import \
        command

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

def _make_hook_decorator(command_name, kind):
    name = "%s_%s" % (kind, command_name)
    def func(help_bypass=True):
        def decorator(f):
            local_dir = os.path.dirname(compat_inspect.stack()[1][1])
            add_to_registry((f, local_dir, help_bypass), name)
            if kind == "post":
                add_to_post_registry((f, local_dir, help_bypass), command_name)
            elif kind == "pre":
                add_to_pre_registry((f, local_dir, help_bypass), command_name)
            else:
                raise ValueError("invalid hook kind %s" % kind)
        return decorator
    func.__name__ = name
    func.__doc__ = """\
Tag the given function as a %(kind)s %(command_name)s hook.

If help_bypass is True, the hook will not be executed if the command is
called in help mode.
""" % {"kind": kind, "command_name": command_name}
    return func

post_configure = _make_hook_decorator("configure", "post")
pre_configure = _make_hook_decorator("configure", "pre")
post_build = _make_hook_decorator("build", "post")
pre_build = _make_hook_decorator("build", "pre")
post_sdist = _make_hook_decorator("sdist", "post")
pre_sdist = _make_hook_decorator("sdist", "pre")

def override(f):
    override_command(f.__name__, f)

def dummy_startup(ctx):
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
