import sys

from bento._config \
    import \
        BENTO_SCRIPT
from bento.compat.api \
    import \
        relpath

from bento.core.options \
    import \
        PackageOptions
from bento.commands.options \
    import \
        OptionsContext
from bento.commands.hooks \
    import \
        get_command_override, get_pre_hooks, get_post_hooks
from bento.commands.configure \
    import \
        _setup_options_parser

def _is_setuptools_activated():
    return "setuptools" in sys.modules

# FIXME: consolidate this code with bentomakerlib
def run_cmd_in_context(cmd_klass, cmd_name, cmd_argv, context_klass, run_node, top_node, package):
    """Run the given Command instance inside its context, including any hook
    and/or override."""
    package_options = PackageOptions.from_file(BENTO_SCRIPT)

    cmd = cmd_klass()
    options_context = OptionsContext.from_command(cmd)
    _setup_options_parser(options_context, package_options)

    context = context_klass(cmd_argv, options_context, package, run_node)
    # FIXME: hack to pass package_options to configure command - most likely
    # this needs to be known in option context ?
    context.package_options = package_options

    if get_command_override(cmd_name):
        cmd_funcs = get_command_override(cmd_name)
    else:
        cmd_funcs = [(cmd.run, top_node.abspath())]

    try:
        def _run_hooks(hook_iter):
            for hook, local_dir, help_bypass in hook_iter:
                local_node = top_node.find_dir(relpath(local_dir, top_node.abspath()))
                context.pre_recurse(local_node)
                try:
                    if not context.help and help_bypass:
                        hook(context)
                finally:
                    context.post_recurse()

        _run_hooks(get_pre_hooks(cmd_name))

        while cmd_funcs:
            cmd_func, local_dir = cmd_funcs.pop(0)
            local_node = top_node.find_dir(relpath(local_dir, top_node.abspath()))
            context.pre_recurse(local_node)
            try:
                cmd_func(context)
            finally:
                context.post_recurse()

        _run_hooks(get_post_hooks(cmd_name))

        cmd.shutdown(context)
    finally:
        context.shutdown()
