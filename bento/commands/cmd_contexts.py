import os
import sys

from bento.core.recurse \
    import \
        NodeRepresentation
from bento.commands.build \
    import \
        build_isection, build_py_isection, build_data_section, _config_content, \
        build_executable
from bento._config \
    import \
        CONFIGURED_STATE_DUMP
from bento.commands.configure \
    import \
        _ConfigureState

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
                raise IOError("%s not found" % CONFIGURED_STATE_DUMP)
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
        self._register_python_files(section_writer)
        self._register_data_files(section_writer)
        self._register_script_files(section_writer)

        self._register_extensions_files(section_writer)
        self._register_libraries_files(section_writer)

    def _register_extensions_files(self, section_writer):
        sections = section_writer.sections["extensions"] = {}
        outputs_e = self._outputs["extensions"]
        for name, extension in self._node_pkg.iter_category("extensions"):
            sections[name] = build_isection(self, name, outputs_e[name], "extensions")

    def _register_libraries_files(self, section_writer):
        sections = section_writer.sections["compiled_libraries"] = {}
        outputs_l = self._outputs["compiled_libraries"]
        for name, library in self._node_pkg.iter_category("libraries"):
            sections[name] = build_isection(self, name, outputs_l[name], "compiled_libraries")

    def _register_python_files(self, section_writer):
        sections = section_writer.sections
        sections["pythonfiles"] = {}

        for name, nodes in self._node_pkg.iter_category("packages"):
            sections["pythonfiles"][name] = build_py_isection(self, name, nodes)
        for name, node in self._node_pkg.iter_category("modules"):
            sections["pythonfiles"][name] = build_py_isection(self, name, [node])
        if self.pkg.config_py:
            content = _config_content(self.get_paths_scheme())
            target_node = self.build_node.make_node(self.pkg.config_py)
            target_node.parent.mkdir()
            target_node.safe_write(content)
            build_py_isection(self, "bento_config", [target_node], self.build_node)

    def _register_data_files(self, section_writer):
        section_writer.sections["datafiles"] = data_sections = {}
        for name, section in self._node_pkg.iter_category("datafiles"):
            data_sections[name] = build_data_section(self, section)

    def _register_script_files(self, section_writer):
        scripts_node = self.build_node.make_node("scripts-%s" % sys.version[:3])
        scripts_node.mkdir()
        section_writer.sections["executables"] = sections = {}
        for name, executable in self.pkg.executables.iteritems():
            sections[name] = build_executable(name, executable, scripts_node)
