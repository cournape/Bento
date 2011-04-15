import os
import sys
import copy
import collections
import cPickle

try:
    from hashlib import md5
except ImportError:
    from md5 import md5

import yaku.context

from bento.core.package_cache \
    import \
        CachedPackage
from bento.core.subpackage \
    import \
        get_extensions, get_compiled_libraries
from bento.commands.configure \
    import \
        _ConfigureState
from bento.commands.errors \
    import \
        UsageException
from bento.commands._config \
    import \
        SCRIPT_NAME
from bento._config \
    import \
        ARGS_CHECKSUM_DB_FILE, CONFIGURED_STATE_DUMP

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
    def __init__(self, cmd_argv, options_context, pkg, top_node):
        self.pkg = pkg

        self.options_context = options_context
        o, a = options_context.parser.parse_args(cmd_argv)
        if o.help:
            self.help = True
        else:
            self.help = False

        self.cmd_argv = cmd_argv
        self.top_node = top_node

        self._configured_state = None

        # Recursive related members
        self.local_node = None
        self.local_pkg = None

    def get_command_arguments(self):
        return self.cmd_argv

    def _get_configured_state(self):
        if self._configured_state is None:
            dump_node = self.top_node.bldnode.find_node(CONFIGURED_STATE_DUMP)
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
        if local_node == self.top_node:
            self.local_node = self.top_node
            return
        else:
            if not local_node.is_src():
                raise IOError("node %r is not in source tree !" % local_node.abspath())
            self.local_node = local_node

            def _get_sub_package():
                k = local_node.find_node("bento.info").path_from(self.top_node)
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
        self.build_root = self.top_node.make_node("build")

class ConfigureContext(_ContextWithBuildDirectory):
    def __init__(self, cmd_argv, options_context, pkg, top_node):
        CmdContext.__init__(self, cmd_argv, options_context, pkg, top_node)

    def setup(self):
        pass

    def shutdown(self):
        CmdContext.shutdown(self)
        CachedPackage.write_checksums()
        _write_argv_checksum(_argv_checksum(sys.argv), "configure")

class DistutilsConfigureContext(ConfigureContext):
    pass

class ConfigureYakuContext(ConfigureContext):
    def __init__(self, cmd_argv, options_context, pkg, top_node):
        super(ConfigureYakuContext, self).__init__(cmd_argv, options_context, pkg, top_node)
        self.yaku_configure_ctx = yaku.context.get_cfg()

    def setup(self):
        extensions = get_extensions(self.pkg, self.top_node)
        libraries = get_compiled_libraries(self.pkg, self.top_node)

        yaku_ctx = self.yaku_configure_ctx
        if extensions or libraries:
            yaku_ctx.use_tools(["ctasks", "pyext"])

    def shutdown(self):
        super(ConfigureYakuContext, self).shutdown()
        self.yaku_configure_ctx.store()

class BuildContext(_ContextWithBuildDirectory):
    def __init__(self, cmd_argv, options_context, pkg, top_node):
        super(BuildContext, self).__init__(cmd_argv, options_context, pkg, top_node)
        self._extensions_callback = {}
        self._clibraries_callback = {}
        self._clibrary_envs = {}
        self._extension_envs = {}

        o, a = options_context.parser.parse_args(cmd_argv)
        if o.inplace:
            self.inplace = True
        else:
            self.inplace = False

    def shutdown(self):
        CmdContext.shutdown(self)
        checksum = _read_argv_checksum("configure")
        _write_argv_checksum(checksum, "build")

    def _compute_extension_name(self, extension_name):
        parent = self.local_node.path_from(self.top_node).split(os.path.sep)
        return ".".join(parent + [extension_name])

    def post_compile(self, section_writer):
        raise NotImplementedError()

    # XXX: none of those register_* really belong here
    def register_builder(self, extension_name, builder):
        full_name = self._compute_extension_name(extension_name)
        self._extensions_callback[full_name] = builder

    def register_clib_builder(self, clib_name, builder):
        relpos = self.local_node.path_from(self.top_node)
        full_name = os.path.join(relpos, clib_name)
        self._clibraries_callback[full_name] = builder

    def register_environment(self, extension_name, env):
        full_name = self._compute_extension_name(extension_name)
        self._extension_envs[full_name] = env

    def register_clib_environment(self, clib_name, env):
        relpos = self.local_node.path_from(self.top_node)
        full_name = os.path.join(relpos, clib_name)
        self._clibrary_envs[full_name] = env

class DistutilsBuildContext(BuildContext):
    def __init__(self, cmd_argv, options_context, pkg, top_node):
        from bento.commands.build_distutils import DistutilsBuilder
        super(DistutilsBuildContext, self).__init__(cmd_argv, options_context, pkg, top_node)

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

        self._distutils_builder = DistutilsBuilder(verbosity=self.verbose)

        self._extensions = copy.deepcopy(self.pkg.extensions)
        self._compiled_libraries = copy.deepcopy(self.pkg.compiled_libraries)

        def build_extension(extension):
            return self._distutils_builder.build_extension(extension)

        def build_compiled_library(library):
            return self._distutils_builder.build_compiled_library(library)

        self._extension_callbacks = collections.defaultdict(lambda : build_extension)
        self._compiled_library_callbacks = collections.defaultdict(lambda : build_compiled_library)

    def post_compile(self, section_writer):
        sections = section_writer.sections
        sections["extensions"] = {}
        sections["compiled_libraries"] = {}

        for name, extension in self._extensions.iteritems():
            builder = self._extension_callbacks[name]
            sections["extensions"][name] = builder(extension)

        for name, compiled_library in self._compiled_libraries.iteritems():
            builder = self._compiled_library_callbacks[name]
            sections["compiled_libraries"][name] = builder(compiled_library)

class BuildYakuContext(BuildContext):
    def __init__(self, cmd_argv, options_context, pkg, top_node):
        super(BuildYakuContext, self).__init__(cmd_argv, options_context, pkg, top_node)
        self.yaku_build_ctx = yaku.context.get_bld()

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

    def shutdown(self):
        super(BuildYakuContext, self).shutdown()
        self.yaku_build_ctx.store()

    def post_compile(self, section_writer):
        sections = section_writer.sections

        builder = self.build_extensions_factory(self.inplace, self.verbose, self.jobs)
        sections["extensions"] = builder(self.pkg)

        builder = self.build_compiled_libraries_factory(self.inplace, self.verbose, self.jobs)
        sections["compiled_libraries"] = builder(self.pkg)

    def build_extensions_factory(self, *a, **kw):
        from bento.commands.build_yaku \
            import \
                build_extensions
        extensions = get_extensions(self.pkg, self.top_node)
        def builder(pkg):
            return build_extensions(extensions,
                    self.yaku_build_ctx, self._extensions_callback,
                    self._extension_envs, *a, **kw)
        return builder

    def build_compiled_libraries_factory(self, *a, **kw):
        from bento.commands.build_yaku \
            import \
                build_compiled_libraries
        libraries = get_compiled_libraries(self.pkg, self.top_node)
        def builder(pkg):
            return build_compiled_libraries(libraries,
                    self.yaku_build_ctx, self._clibraries_callback,
                    self._clibrary_envs, *a, **kw)
        return builder

def _argv_checksum(argv):
    return md5(cPickle.dumps(argv)).hexdigest()

def _read_argv_checksum(cmd_name):
    fid = open(ARGS_CHECKSUM_DB_FILE, "rb")
    try:
        data = cPickle.load(fid)
        return data[cmd_name]
    finally:
        fid.close()

def _write_argv_checksum(checksum, cmd_name):
    if os.path.exists(ARGS_CHECKSUM_DB_FILE):
        fid = open(ARGS_CHECKSUM_DB_FILE, "rb")
        try:
            data = cPickle.load(fid)
        finally:
            fid.close()
    else:
        data = {}

    data[cmd_name] = checksum
    fid = open(ARGS_CHECKSUM_DB_FILE, "wb")
    try:
        cPickle.dump(data, fid)
    finally:
        fid.close()

CONTEXT_REGISTRY = ContextRegistry()
