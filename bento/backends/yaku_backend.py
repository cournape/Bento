import os.path as op

from bento.utils.utils \
    import \
        extract_exception
from bento.core.node_package \
    import \
        translate_name
from bento.core.subpackage \
    import \
        get_extensions, get_compiled_libraries
from bento.commands.command_contexts \
    import \
        ConfigureContext, BuildContext
from bento.errors \
    import \
        ConfigurationError
from bento.backends.core \
    import \
        AbstractBackend

import yaku.context
import yaku.errors

class ConfigureYakuContext(ConfigureContext):
    def __init__(self, global_context, cmd_argv, options_context, pkg, run_node):
        super(ConfigureYakuContext, self).__init__(global_context, cmd_argv, options_context, pkg, run_node)
        build_path = run_node._ctx.bldnode.path_from(run_node)
        source_path = run_node._ctx.srcnode.path_from(run_node)
        self.yaku_context = yaku.context.get_cfg(src_path=source_path, build_path=build_path)

    def configure(self):
        extensions = get_extensions(self.pkg, self.run_node)
        libraries = get_compiled_libraries(self.pkg, self.run_node)

        yaku_ctx = self.yaku_context
        if extensions or libraries:
            for t in ["ctasks", "pyext"]:
                try:
                    yaku_ctx.use_tools([t])
                except yaku.errors.ConfigurationFailure:
                    e = extract_exception()
                    raise ConfigurationError(str(e))

    def finish(self):
        super(ConfigureYakuContext, self).finish()
        self.yaku_context.store()

    def pre_recurse(self, local_node):
        super(ConfigureYakuContext, self).pre_recurse(local_node)
        self._old_path = self.yaku_context.path
        self.yaku_context.path = self.yaku_context.path.make_node(self.local_node.path_from(self.top_node))

    def post_recurse(self):
        self.yaku_context.path = self._old_path
        super(ConfigureYakuContext, self).post_recurse()

class BuildYakuContext(BuildContext):
    def __init__(self, global_context, cmd_argv, options_context, pkg, run_node):
        from bento.commands.build_yaku import build_extension, build_compiled_library

        super(BuildYakuContext, self).__init__(global_context, cmd_argv, options_context, pkg, run_node)
        build_path = run_node._ctx.bldnode.path_from(run_node)
        source_path = run_node._ctx.srcnode.path_from(run_node)
        self.yaku_context = yaku.context.get_bld(src_path=source_path, build_path=build_path)

        o, a = options_context.parser.parse_args(cmd_argv)
        if o.jobs:
            jobs = int(o.jobs)
        else:
            jobs = 1
        self.verbose = o.verbose
        self.jobs = jobs

        def _builder_factory(category, builder):
            def _build(extension, include_dirs=None, **kw):
                env = kw.get("env", {})
                if include_dirs:
                    env["include_dirs"] = include_dirs

                outputs = builder(self.yaku_context, extension, env=env)
                nodes = [self.build_node.make_node(o) for o in outputs]

                p = self.build_node.find_node(nodes[0].parent.bldpath())
                relative_name = extension.name.rsplit(".")[-1]
                full_name = translate_name(relative_name, p, self.build_node)

                from_node = p
                pkg_dir = op.dirname(full_name.replace('.', op.sep))
                target_dir = op.join('$sitedir', pkg_dir)
                self.outputs_registry.register_outputs(category, full_name, nodes,
                                                       from_node, target_dir)
            return _build

        self.builder_registry.register_category("extensions",
            _builder_factory("extensions", build_extension))
        self.builder_registry.register_category("compiled_libraries",
            _builder_factory("compiled_libraries", build_compiled_library))

    def finish(self):
        super(BuildYakuContext, self).finish()
        self.yaku_context.store()

    def compile(self):
        super(BuildYakuContext, self).compile()

        import yaku.task_manager
        bld = self.yaku_context
        bld.env["VERBOSE"] = self.verbose

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
        self._old_path = self.yaku_context.path
        # FIXME: we should not modify yaku context, but add current node +
        # recurse support to yaku instead
        # Gymnastic to make a *yaku* node from a *bento* node
        self.yaku_context.path = self.yaku_context.path.make_node(self.local_node.path_from(self.top_node))

    def post_recurse(self):
        self.yaku_context.path = self._old_path
        super(BuildYakuContext, self).post_recurse()

class YakuBackend(AbstractBackend):
    def register_command_contexts(self, context):
        context.register_command_context("configure", ConfigureYakuContext)
        context.register_command_context("build", BuildYakuContext)
