import os
import sys
import re

from bento.compat \
    import \
        inspect as compat_inspect
from bento.commands.core \
    import \
        command
from bento.core.utils \
    import \
        extract_exception

SAFE_MODULE_NAME = re.compile("[^a-zA-Z_]")

class HookRegistry(object):
    def __init__(self):
        self._pre_hooks = {}
        self._post_hooks = {}

    def add_pre_hook(self, hook, cmd_name):
        if cmd_name in self._pre_hooks:
            self._pre_hooks[cmd_name].append(hook)
        else:
            self._pre_hooks[cmd_name] = [hook]

    def add_post_hook(self, hook, cmd_name):
        if cmd_name in self._post_hooks:
            self._post_hooks[cmd_name].append(hook)
        else:
            self._post_hooks[cmd_name] = [hook]

    def retrieve_pre_hooks(self, cmd_name):
        return self._pre_hooks.get(cmd_name, [])

    def retrieve_post_hooks(self, cmd_name):
        return self._post_hooks.get(cmd_name, [])

__COMMANDS_OVERRIDE = {}
__INIT_FUNCS = {}

def override_command(command, func):
    global __COMMANDS_OVERRIDE
    local_dir = os.path.dirname(compat_inspect.stack()[2][1])

    if __COMMANDS_OVERRIDE.has_key(command):
        __COMMANDS_OVERRIDE[command].append((func, local_dir))
    else:
        __COMMANDS_OVERRIDE[command] = [(func, local_dir)]

def find_pre_hooks(modules, cmd_name):
    """Retrieve all pre hooks instances defined in given modules list.

    This should be used to find prehooks defined through the hook.pre_*. This
    works by looking for all WrappedCommand instances in the modules.

    Parameters
    ----------
    modules: seq
        list of modules to look into
    cmd_name: str
        command name
    """
    pre_hooks = []
    for module in modules:
        yo = [f for f in vars(module).values() if isinstance(f, PreHookWrapper)]
        pre_hooks.extend([f for f in vars(module).values() if isinstance(f,
            PreHookWrapper) and f.cmd_name == cmd_name])
    return pre_hooks

def find_post_hooks(modules, cmd_name):
    """Retrieve all post hooks instances defined in given modules list.

    This should be used to find prehooks defined through the hook.pre_*. This
    works by looking for all WrappedCommand instances in the modules.

    Parameters
    ----------
    modules: seq
        list of modules to look into
    cmd_name: str
        command name
    """
    post_hooks = []
    for module in modules:
        post_hooks.extend([f for f in vars(module).values() if isinstance(f,
            PostHookWrapper) and f.cmd_name == cmd_name])
    return post_hooks

def get_command_override(cmd_name):
    global __COMMANDS_OVERRIDE
    return __COMMANDS_OVERRIDE.get(cmd_name, [])

class _HookWrapperBase(object):
    def __init__(self, func, cmd_name, local_dir):
        self._func = func
        self.local_dir = local_dir
        self.cmd_name = cmd_name
        self.name = func.__name__

    def __call__(self, ctx):
        return self._func(ctx)

    def __getattr__(self, k):
        return getattr(self._func, k)

class PreHookWrapper(_HookWrapperBase):
    pass

class PostHookWrapper(_HookWrapperBase):
    pass

def _make_hook_decorator(command_name, kind):
    name = "%s_%s" % (kind, command_name)
    help_bypass = False
    def decorator(f):
        local_dir = os.path.dirname(compat_inspect.stack()[1][1])
        if kind == "post":
            hook = PostHookWrapper(f, command_name, local_dir)
        elif kind == "pre":
            hook = PreHookWrapper(f, command_name, local_dir)
        else:
            raise ValueError("invalid hook kind %s" % kind)
        return hook
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
        try:
            exec(compile(code, main_file, 'exec'), module.__dict__)
            sys.modules[module_name] = module
        except SyntaxError:
            e = extract_exception()
            raise SyntaxError("Invalid syntax in hook file %s, line %s" % (main_file, e.lineno))
    finally:
        sys.path.pop(0)

    module.root_path = main_file
    if not "startup" in __INIT_FUNCS:
        module.startup = dummy_startup
    else:
        module.startup = __INIT_FUNCS["startup"]
    if not "options" in __INIT_FUNCS:
        module.options = dummy_options
    else:
        module.options = __INIT_FUNCS["options"]
    if not "shutdown" in __INIT_FUNCS:
        module.shutdown = dummy_shutdown
    else:
        module.shutdown = __INIT_FUNCS["shutdown"]

    return module
