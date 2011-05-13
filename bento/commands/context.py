import os
import sys
import collections
import cPickle

try:
    from hashlib import md5
except ImportError:
    from md5 import md5

import yaku.context

from bento.core.subpackage \
    import \
        get_extensions, get_compiled_libraries
from bento.core.recurse \
    import \
        NodeRepresentation
from bento.commands.configure \
    import \
        _ConfigureState
from bento.commands.build \
    import \
        build_isection
from bento.commands.errors \
    import \
        UsageException
from bento.commands._config \
    import \
        SCRIPT_NAME
from bento._config \
    import \
        CONFIGURED_STATE_DUMP

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

class DummyContextManager(object):
    def __init__(self, pre, post):
        self.pre = pre
        self.post = post

    def __enter__(self):
        self.pre()

    def __exit__(self, *a, **kw):
        self.post()

class CmdContext(object):
    def __init__(self, cmd_argv, options_context, pkg, run_node):
        self.pkg = pkg

        self.options_context = options_context
        o, a = options_context.parser.parse_args(cmd_argv)
        if o.help:
            self.help = True
        else:
            self.help = False

        self.cmd_argv = cmd_argv

        # CWD node
        self.run_node = run_node
        # Top source node (the one containing the top bento.info)
        # TODO: kept for compatibility. Remove it ?
        if run_node is not None:
            self.top_node = run_node._ctx.srcnode
            self.build_node = run_node._ctx.bldnode
            # cur_node refers to the current path when recursing into sub directories
            self.cur_node = self.top_node
        else:
            self.top_node = None
            self.build_node = None

        self._configured_state = None

        # Recursive related members
        self.local_node = None
        self.local_pkg = None

    def get_command_arguments(self):
        return self.cmd_argv

    def _get_configured_state(self):
        if self._configured_state is None:
            dump_node = self.build_node.find_node(CONFIGURED_STATE_DUMP)
            if dump_node is None:
                raise UsageException(
                       "You need to run %s configure before building" % SCRIPT_NAME)
            else:
                self._configured_state = _ConfigureState.from_dump(dump_node)
        return self._configured_state

    def get_package(self):
        state = self._get_configured_state()
        return state.pkg

    def get_user_data(self):
        state = self._get_configured_state()
        return state.user_data

    def get_paths_scheme(self):
        state = self._get_configured_state()
        return state.paths

    def recurse_manager(self, local_node):
        """
        Return a dummy object to use for recurse if one wants to use context
        manager. Example::

            with context.recurse_manager(local_node):
                func(context)
        """
        return DummyContextManager(lambda: self.pre_recurse(local_node),
                                   lambda: self.post_recurse())

    def pre_recurse(self, local_node):
        """
        Note
        ----
        Every call to pre_recurse should be followed by a call to post_recurse.

        Calling pre_recurse for the top hook node must work as well (but could
        do nothing)
        """
        if local_node == self.run_node:
            self.local_node = self.run_node
            return
        else:
            if not local_node.is_src():
                raise IOError("node %r is not in source tree !" % local_node.abspath())
            self.local_node = local_node

            def _get_sub_package():
                k = local_node.find_node("bento.info").path_from(self.run_node)
                if k is None:
                    raise IOError("%r not found" % os.path.join(local_node.abspath(), "bento.info"))
                else:
                    return self.pkg.subpackages.get(k, None)
            self.local_pkg = _get_sub_package()

    def post_recurse(self):
        # Setting those to None is not strictly necessary, but this makes
        # things more consistent for debugging (context state exactly same
        # before pre_recurse and after post_recurse
        self.local_node = None
        self.local_pkg = None

    def init(self):
        pass

    def shutdown(self):
        pass

class HelpContext(CmdContext):
    pass

class _ContextWithBuildDirectory(CmdContext):
    def __init__(self, *a, **kw):
        CmdContext.__init__(self, *a, **kw)
        self.build_root = self.run_node.make_node("build")

class ConfigureContext(_ContextWithBuildDirectory):
    def __init__(self, cmd_argv, options_context, pkg, run_node):
        CmdContext.__init__(self, cmd_argv, options_context, pkg, run_node)

    def setup(self):
        pass

    def shutdown(self):
        CmdContext.shutdown(self)

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

class BuildContext(_ContextWithBuildDirectory):
    def __init__(self, cmd_argv, options_context, pkg, run_node):
        super(BuildContext, self).__init__(cmd_argv, options_context, pkg, run_node)
        # Those are dummies - are set by subclasses
        self._extension_callbacks = None
        self._compiled_library_callbacks = None

        self._outputs = {}

        self._node_pkg = NodeRepresentation(run_node, self.top_node)
        self._node_pkg.update_package(pkg)

    def shutdown(self):
        CmdContext.shutdown(self)

    def _compute_extension_name(self, extension_name):
        if self.local_node is None:
            raise ValueError("Forgot to call pre_recurse ?")
        if self.local_node != self.top_node:
            parent = self.local_node.srcpath().split(os.path.sep)
            return ".".join(parent + [extension_name])
        else:
            return extension_name

    def register_builder(self, extension_name, builder):
        full_name = self._compute_extension_name(extension_name)
        self._extension_callbacks[full_name] = builder

    def register_compiled_library_builder(self, clib_name, builder):
        relpos = self.local_node.path_from(self.top_node)
        full_name = os.path.join(relpos, clib_name).replace(os.sep, ".")
        self._compiled_library_callbacks[full_name] = builder

    def compile(self):
        raise NotImplementedError()

    def post_compile(self, section_writer):
        sections = section_writer.sections
        sections["extensions"] = {}
        sections["compiled_libraries"] = {}

        outputs_e, outputs_c = self._outputs["extensions"], self._outputs["compiled_libraries"]
        for name, extension in self._node_pkg.iter_category("extensions"):
            sections["extensions"][name] = build_isection(self, name, outputs_e[name], "extensions")
        for name, extension in self._node_pkg.iter_category("libraries"):
            sections["compiled_libraries"][name] = build_isection(self, name,
                        outputs_c[name], "compiled_libraries")

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

        def build_extension(extension):
            return self._distutils_builder.build_extension(extension)

        def build_compiled_library(library):
            return self._distutils_builder.build_compiled_library(library)

        self._extension_callbacks = collections.defaultdict(lambda : build_extension)
        self._compiled_library_callbacks = collections.defaultdict(lambda : build_compiled_library)

    def compile(self):
        outputs = {}
        for name, extension in self._node_pkg.iter_category("extensions"):
            builder = self._extension_callbacks[name]
            extension = extension.extension_from(extension.ref_node)
            outputs[name] = builder(extension)
        self._outputs["extensions"] = outputs

        outputs = {}
        for name, compiled_library in self._node_pkg.iter_category("libraries"):
            builder = self._compiled_library_callbacks[name]
            compiled_library = compiled_library.extension_from(compiled_library.ref_node)
            outputs[name] = builder(compiled_library)
        self._outputs["compiled_libraries"] = outputs

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
        def _build_extension(extension):
            return build_extension(self.yaku_build_ctx, extension, verbose)
        def _build_compiled_library(library):
            return build_compiled_library(self.yaku_build_ctx, library, verbose)
        self._extension_callbacks = collections.defaultdict(lambda : _build_extension)
        self._compiled_library_callbacks = collections.defaultdict(lambda : _build_compiled_library)

    def shutdown(self):
        super(BuildYakuContext, self).shutdown()
        self.yaku_build_ctx.store()

    def compile(self):
        import yaku.task_manager
        bld = self.yaku_build_ctx

        outputs_e = {}
        for name, extension in self._node_pkg.iter_category("extensions"):
            builder = self._extension_callbacks[name]
            self.pre_recurse(extension.ref_node)
            try:
                extension = extension.extension_from(extension.ref_node)
                outputs_e[name] = builder(extension)
            finally:
                self.post_recurse()

        outputs_c = {}
        for name, compiled_library in self._node_pkg.iter_category("libraries"):
            builder = self._compiled_library_callbacks[name]
            self.pre_recurse(compiled_library.ref_node)
            try:
                compiled_library = compiled_library.extension_from(compiled_library.ref_node)
                outputs_c[name] = builder(compiled_library)
            finally:
                self.post_recurse()

        task_manager = yaku.task_manager.TaskManager(bld.tasks)
        if self.jobs < 2:
            runner = yaku.scheduler.SerialRunner(bld, task_manager)
        else:
            runner = yaku.scheduler.ParallelRunner(bld, task_manager, self.jobs)
        runner.start()
        runner.run()

        self._outputs["extensions"] = outputs_e
        self._outputs["compiled_libraries"] = outputs_c

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
