import os

from bento.compat.api \
    import \
        relpath

from bento.commands.hooks \
    import \
        create_hook_module

def resolve_and_run_command(global_context, cmd, cmd_name, cmd_argv, context_klass,
        run_node, top_node, package, package_options):
    """Run the given Command instance inside its context, including any hook
    and/or override."""
    options_context = global_context.retrieve_options_context(cmd_name)

    context = context_klass(global_context, cmd_argv, options_context, package, run_node)
    # FIXME: hack to pass package_options to configure command - most likely
    # this needs to be known in option context ?
    context.package_options = package_options

    pre_hooks = global_context.retrieve_pre_hooks(cmd_name)
    post_hooks = global_context.retrieve_post_hooks(cmd_name)

    run_command_in_context(context, cmd, pre_hooks, post_hooks)

    return cmd, context

def run_command_in_context(context, cmd, pre_hooks=None, post_hooks=None):
    """Run the given command instance with the hooks within its context. """
    if pre_hooks is None:
        pre_hooks = []
    if post_hooks is None:
        post_hooks = []

    top_node = context.top_node
    cmd_funcs = [(cmd.run, top_node.abspath())]

    def _run_hooks(hooks):
        for hook in hooks:
            local_node = top_node.find_dir(relpath(hook.local_dir, top_node.abspath()))
            context.pre_recurse(local_node)
            try:
                if not context.help:
                    hook(context)
            finally:
                context.post_recurse()

    context.init()
    try:
        cmd.init(context)

        _run_hooks(pre_hooks)

        context.configure()

        while cmd_funcs:
            cmd_func, local_dir = cmd_funcs.pop(0)
            local_node = top_node.find_dir(relpath(local_dir, top_node.abspath()))
            context.pre_recurse(local_node)
            try:
                cmd_func(context)
            finally:
                context.post_recurse()

        _run_hooks(post_hooks)

        cmd.finish(context)
    finally:
        context.finish()

    return cmd, context

def set_main(pkg, top_node, build_node):
    modules = []
    hook_files = pkg.hook_files
    for name, spkg in pkg.subpackages.items():
        hook_files.extend([os.path.join(spkg.rdir, h) for h in spkg.hook_files])

    # TODO: find doublons
    for f in hook_files:
        hook_node = top_node.make_node(f)
        if hook_node is None or not os.path.exists(hook_node.abspath()):
            raise ValueError("Hook file %s not found" % f)
        modules.append(create_hook_module(hook_node.abspath()))
    return modules
