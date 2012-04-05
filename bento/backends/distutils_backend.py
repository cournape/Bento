import os.path as op

from bento.backends.core \
    import \
        AbstractBackend
from bento.commands.command_contexts \
    import \
        ConfigureContext, BuildContext

class DistutilsConfigureContext(ConfigureContext):
    pass

class DistutilsBuildContext(BuildContext):
    def __init__(self, global_context, cmd_argv, options_context, pkg, run_node):
        from bento.commands.build_distutils import DistutilsBuilder
        super(DistutilsBuildContext, self).__init__(global_context, cmd_argv, options_context, pkg, run_node)

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
            def _build(extension, **kw):
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

class DistutilsBackend(AbstractBackend):
    def register_command_contexts(self, context):
        context.register_command_context("configure", DistutilsConfigureContext)
        context.register_command_context("build", DistutilsBuildContext)
