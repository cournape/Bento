import os.path as op

import yaku.context

from bento.core.subpackage \
    import \
        get_extensions, get_compiled_libraries
from bento.commands.cmd_contexts \
    import \
        CmdContext, ConfigureContext, BuildContext

class ContextRegistry(object):
    def __init__(self, default=None):
        self._contexts = {}
        self.set_default(default)

    def set_default(self, default):
        self._default = default

    def is_registered(self, name):
        return name in self._contexts

    def register(self, name, context):
        if self._contexts.has_key(name):
            raise ValueError("context for command %r already registered !" % name)
        else:
            self._contexts[name] = context

    def get(self, name):
        context = self._contexts.get(name, None)
        if context is None:
            if self._default is None:
                raise ValueError("No context registered for command %r" % name)
            else:
                return self._default
        else:
            return context

class GlobalContext(object):
    def __init__(self, commands_registry, contexts_registry, options_registry, commands_scheduler):
        self._commands_registry = commands_registry
        self._contexts_registry = contexts_registry
        self._options_registry = options_registry
        self._scheduler = commands_scheduler

    def register_command(self, name, klass):
        self._commands_registry.register_command(name, klass)

    def register_context(self, name, klass):
        self._contexts_registry.register(name, klass)

    def add_option(self, cmd_name, option, group=None):
        ctx = self._options_registry.get_options(cmd_name)
        ctx.add_option(option, group)

    def set_before(self, cmd_name, cmd_name_before):
        """Specify that command cmd_name_before should run before cmd_name."""
        self._scheduler.set_before(cmd_name, cmd_name_before)

    def set_after(self, cmd_name, cmd_name_after):
        """Specify that command cmd_name_before should run after cmd_name."""
        self._scheduler.set_after(cmd_name, cmd_name_after)

class HelpContext(CmdContext):
    pass

class DistutilsConfigureContext(ConfigureContext):
    pass

class ConfigureYakuContext(ConfigureContext):
    def __init__(self, cmd_argv, options_context, pkg, run_node):
        super(ConfigureYakuContext, self).__init__(cmd_argv, options_context, pkg, run_node)
        build_path = run_node._ctx.bldnode.path_from(run_node)
        source_path = run_node._ctx.srcnode.path_from(run_node)
        self.yaku_configure_ctx = yaku.context.get_cfg(src_path=source_path, build_path=build_path)

    def setup(self):
        extensions = get_extensions(self.pkg, self.run_node)
        libraries = get_compiled_libraries(self.pkg, self.run_node)

        yaku_ctx = self.yaku_configure_ctx
        if extensions or libraries:
            yaku_ctx.use_tools(["ctasks", "pyext"])

    def shutdown(self):
        super(ConfigureYakuContext, self).shutdown()
        self.yaku_configure_ctx.store()

    def pre_recurse(self, local_node):
        super(ConfigureYakuContext, self).pre_recurse(local_node)
        self._old_path = self.yaku_configure_ctx.path
        # Gymnastic to make a *yaku* node from a *bento* node
        self.yaku_configure_ctx.path = self.yaku_configure_ctx.path.make_node(self.local_node.path_from(self.run_node))

    def post_recurse(self):
        self.yaku_configure_ctx.path = self._old_path
        super(ConfigureYakuContext, self).post_recurse()

class DistutilsBuildContext(BuildContext):
    def __init__(self, cmd_argv, options_context, pkg, run_node):
        from bento.commands.build_distutils import DistutilsBuilder
        super(DistutilsBuildContext, self).__init__(cmd_argv, options_context, pkg, run_node)

        o, a = options_context.parser.parse_args(cmd_argv)
        if o.jobs:
            jobs = int(o.jobs)
        else:
            jobs = 1
        if o.verbose:
            verbose = int(o.verbose)
        else:
            verbose = 0
        self.verbose = verbose
        self.jobs = jobs

        build_path = self.build_node.path_from(self.run_node)
        self._distutils_builder = DistutilsBuilder(verbosity=self.verbose, build_base=build_path)

        def _builder_factory(category, builder):
            def _build(extension):
                outputs = builder(extension)
                nodes = [self.build_node.find_node(o) for o in outputs]
                from_node = self.build_node

                pkg_dir = op.dirname(extension.name.replace('.', op.sep))
                target_dir = op.join('$sitedir', pkg_dir)
                self.outputs_registry.register_outputs(category, extension.name, nodes,
                                                       from_node, target_dir)
            return _build

        self.builder_registry.register_category("extensions", 
            _builder_factory("extensions", self._distutils_builder.build_extension))
        self.builder_registry.register_category("compiled_libraries",
            _builder_factory("compiled_libraries", self._distutils_builder.build_compiled_library))

    def compile(self):
        super(DistutilsBuildContext, self).compile()
        reg = self.builder_registry
        for category in ("extensions", "compiled_libraries"):
            for name, extension in self._node_pkg.iter_category(category):
                builder = reg.builder(category, name)
                extension = extension.extension_from(extension.ref_node)
                builder(extension)

class BuildYakuContext(BuildContext):
    def __init__(self, cmd_argv, options_context, pkg, run_node):
        super(BuildYakuContext, self).__init__(cmd_argv, options_context, pkg, run_node)
        build_path = run_node._ctx.bldnode.path_from(run_node)
        source_path = run_node._ctx.srcnode.path_from(run_node)
        self.yaku_build_ctx = yaku.context.get_bld(src_path=source_path, build_path=build_path)

        o, a = options_context.parser.parse_args(cmd_argv)
        if o.jobs:
            jobs = int(o.jobs)
        else:
            jobs = 1
        if o.verbose:
            verbose = int(o.verbose)
        else:
            verbose = 0
        self.verbose = verbose
        self.jobs = jobs

        from bento.commands.build_yaku import build_extension, build_compiled_library

        def _builder_factory(category, builder):
            def _build(extension):
                outputs = builder(self.yaku_build_ctx, extension, verbose)
                nodes = [self.build_node.make_node(o) for o in outputs]
                from_node = self.build_node

                pkg_dir = op.dirname(extension.name.replace('.', op.sep))
                target_dir = op.join('$sitedir', pkg_dir)
                self.outputs_registry.register_outputs(category, extension.name, nodes,
                                                       from_node, target_dir)
            return _build

        self.builder_registry.register_category("extensions",
            _builder_factory("extensions", build_extension))
        self.builder_registry.register_category("compiled_libraries",
            _builder_factory("compiled_libraries", build_compiled_library))

    def shutdown(self):
        super(BuildYakuContext, self).shutdown()
        self.yaku_build_ctx.store()

    def compile(self):
        super(BuildYakuContext, self).compile()

        import yaku.task_manager
        bld = self.yaku_build_ctx

        reg = self.builder_registry

        for category in ["extensions", "compiled_libraries"]:
            for name, item in self._node_pkg.iter_category(category):
                builder = reg.builder(category, name)
                self.pre_recurse(item.ref_node)
                try:
                    item = item.extension_from(item.ref_node)
                    builder(item)
                finally:
                    self.post_recurse()

        task_manager = yaku.task_manager.TaskManager(bld.tasks)
        if self.jobs < 2:
            runner = yaku.scheduler.SerialRunner(bld, task_manager)
        else:
            runner = yaku.scheduler.ParallelRunner(bld, task_manager, self.jobs)
        runner.start()
        runner.run()

        # TODO: inplace support

    def pre_recurse(self, local_node):
        super(BuildYakuContext, self).pre_recurse(local_node)
        self._old_path = self.yaku_build_ctx.path
        # FIXME: we should not modify yaku context src_root, but add current
        # node + recurse support to yaku instead
        # Gymnastic to make a *yaku* node from a *bento* node
        self.yaku_build_ctx.path = self.yaku_build_ctx.path.make_node(self.local_node.path_from(self.top_node))

    def post_recurse(self):
        self.yaku_build_ctx.path = self._old_path
        super(BuildYakuContext, self).post_recurse()


CONTEXT_REGISTRY = ContextRegistry()
