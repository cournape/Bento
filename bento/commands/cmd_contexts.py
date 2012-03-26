import os
import sys
import string

import os.path as op

from bento.core.errors \
    import \
        InvalidPackage
from bento.core.utils \
    import \
        is_string, subst_vars
from bento.compat.api \
    import \
        defaultdict
from bento.core.node_package \
    import \
        NodeRepresentation
from bento.commands.build \
    import \
        _config_content
from bento.core.meta \
    import \
        PackageMetadata
from bento.commands.script_utils \
    import \
        create_posix_script, create_win32_script
from bento._config \
    import \
        CONFIGURED_STATE_DUMP
from bento.commands.configure \
    import \
        _ConfigureState, _compute_scheme
from bento.commands.build \
    import \
        SectionWriter
from bento.commands.install \
    import \
        copy_installer
from bento.installed_package_description \
    import \
        InstalledSection

class DummyContextManager(object):
    def __init__(self, pre, post):
        self.pre = pre
        self.post = post

    def __enter__(self):
        self.pre()

    def __exit__(self, *a, **kw):
        self.post()

class CmdContext(object):
    def __init__(self, global_context, cmd_argv, options_context, pkg, run_node):
        self._global_context = global_context
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

        if self.pkg.sub_directory:
            self.top_or_sub_directory_node = self.top_node.make_node(self.pkg.sub_directory)
            self.build_or_sub_directory_node = self.build_node.make_node(self.pkg.sub_directory)
        else:
            self.top_or_sub_directory_node = self.top_node
            self.build_or_sub_directory_node = self.build_node

        self._configured_state = None

        # Recursive related members
        self.local_node = None
        self.local_pkg = None

    def make_source_node(self, path):
        n = self.top_node.find_node(path)
        if n is None:
            raise IOError("file %s not found" % (op.join(self.top_node.abspath(), path)))
        else:
            return n

    def make_build_node(self, path):
        n = self.build_node.make_node(path)
        n.parent.mkdir()
        return n

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
                relative_pos = local_node.path_from(self.top_or_sub_directory_node)
                local_bento = self.top_node.find_node(op.join(relative_pos, "bento.info"))
                k = local_bento.path_from(self.run_node)
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
    def __init__(self, global_context, cmd_argv, options_context, pkg, run_node):
        CmdContext.__init__(self, global_context, cmd_argv, options_context, pkg, run_node)

    def setup(self):
        pass

    def shutdown(self):
        CmdContext.shutdown(self)

class _Dummy(object):
    pass

class _RegistryBase(object):
    """A simple registry of sets of callbacks, one set per category."""
    def __init__(self):
        self._callbacks = {}
        self.categories = _Dummy()

    def register_category(self, category, default_builder):
        if category in self._callbacks:
            raise ValueError("Category %r already registered" % category)
        else:
            self._callbacks[category] = defaultdict(lambda: default_builder)
            setattr(self.categories, category, _Dummy())

    def register_callback(self, category, name, builder):
        c = self._callbacks.get(category, None)
        if c is not None:
            c[name] = builder
            cat = getattr(self.categories, category)
            setattr(cat, name, builder)
        else:
            raise ValueError("category %s is not registered yet" % category)

    def callback(self, category, name):
        if not category in self._callbacks:
            raise ValueError("Unregistered category %r" % category)
        else:
            return self._callbacks[category][name]

    def default_callback(self, category, *a, **kw):
        if not category in self._callbacks:
            raise ValueError("Unregistered category %r" % category)
        else:
            return self._callbacks[category].default_factory()(*a, **kw)

class BuilderRegistry(_RegistryBase):
    builder = _RegistryBase.callback

class ISectionRegistry(_RegistryBase):
    registrer = _RegistryBase.callback

class OutputRegistry(object):
    def __init__(self, categories=None):
        self.categories = {}
        self.installed_categories = {}
        if categories:
            for category, installed_category in categories:
                self.register_category(category, installed_category)

    def register_category(self, category, installed_category):
        if category in self.categories:
            raise ValueError("Category %r already registered")
        else:
            self.categories[category] = {}
            self.installed_categories[category] = installed_category

    def register_outputs(self, category, name, nodes, from_node, target_dir):
        if not category in self.categories:
            raise ValueError("Unknown category %r" % category)
        else:
            cat = self.categories[category]
            if name in cat:
                raise ValueError("Outputs for categoryr=%r and name=%r already registered" % (category, name))
            else:
                cat[name] = (nodes, from_node, target_dir)

    def iter_category(self, category):
        if not category in self.categories:
            raise ValueError("Unknown category %r" % category)
        else:
            for k, v in self.categories[category].items():
                yield k, v[0], v[1], v[2]

    def iter_over_category(self):
        for category in self.categories:
            for name, nodes, from_node, target_dir in self.iter_category(category):
                yield category, name, nodes, from_node, target_dir

def _generic_iregistrer(category, name, nodes, from_node, target_dir):
    source_dir = os.path.join("$_srcrootdir", from_node.bldpath())
    files = [n.path_from(from_node) for n in nodes]
    return InstalledSection.from_source_target_directories(
        category, name, source_dir, target_dir, files)

def fill_metadata_template(content, pkg):
    tpl = string.Template(content)
    meta = PackageMetadata.from_package(pkg)

    def _safe_repr(val):
        # FIXME: actually not safe at all. Needs to escape and all.
        if is_string(val):
            if len(val.splitlines()) > 1:
                return '"""%s"""' % (val,)
            else:
                return '"%s"' % (val,)
        else:
            return repr(val)

    meta_dict = dict([(k.upper(), _safe_repr(getattr(meta, k))) for k in meta.metadata_attributes])

    return tpl.substitute(meta_dict)

def write_template(top_node, pkg):
    source = top_node.find_node(pkg.meta_template_file)
    if source is None:
        raise InvalidPackage("File %r not found (defined in 'MetaTemplateFile' field)" \
                             % (pkg.meta_template_file,))
    source_content = source.read()
    output_content = fill_metadata_template(source_content, pkg)

    output = source.change_ext("")
    output.safe_write(output_content)
    return output

class BuildContext(_ContextWithBuildDirectory):
    def __init__(self, global_context, cmd_argv, options_context, pkg, run_node):
        super(BuildContext, self).__init__(global_context, cmd_argv, options_context, pkg, run_node)
        self.builder_registry = BuilderRegistry()
        self.section_writer = SectionWriter()

        o, a = self.options_context.parser.parse_args(cmd_argv)
        if o.inplace:
            self.inplace = True
        else:
            self.inplace = False
        # Builders signature:
        #   - first argument: name, str. Name of the entity to be built
        #   - second argument: object. Value returned by
        #   NodePackage.iter_category for this category

        # TODO: # Refactor builders so that they directoy register outputs
        # instead of returning stuff to be registered (to allow for "delayed"
        # registration)
        def data_section_builder(name, section):
            return name, section.nodes, section.ref_node, section.target_dir

        def package_builder(name, node_py_package):
            return name, node_py_package.nodes, self.top_or_sub_directory_node, "$sitedir"

        def module_builder(name, node):
            return name, [node], self.top_or_sub_directory_node, "$sitedir"

        def script_builder(name, executable):
            scripts_node = self.build_node.make_node("scripts-%s" % sys.version[:3])
            scripts_node.mkdir()
            if sys.platform == "win32":
                nodes = create_win32_script(name, executable, scripts_node)
            else:
                nodes = create_posix_script(name, executable, scripts_node)
            return name, nodes, scripts_node, "$bindir"

        self.builder_registry.register_category("datafiles", data_section_builder)
        self.builder_registry.register_category("packages", package_builder)
        self.builder_registry.register_category("modules", module_builder)
        self.builder_registry.register_category("scripts", script_builder)

        if self.pkg.sub_directory is not None:
            sub_directory_node = self.top_node.find_node(self.pkg.sub_directory)
        else:
            sub_directory_node = None
        self._node_pkg = NodeRepresentation(run_node, self.top_node, sub_directory_node)
        self._node_pkg.update_package(pkg)

        categories = (("packages", "pythonfiles"), ("modules", "pythonfiles"), ("datafiles", "datafiles"),
                      ("scripts", "executables"), ("extensions", "extensions"),
                      ("compiled_libraries", "compiled_libraries"))
        self.outputs_registry = OutputRegistry(categories)

        self.isection_registry = ISectionRegistry()
        self.isection_registry.register_category("extensions", _generic_iregistrer)
        self.isection_registry.register_category("compiled_libraries", _generic_iregistrer)
        self.isection_registry.register_category("packages", _generic_iregistrer)
        self.isection_registry.register_category("modules", _generic_iregistrer)
        self.isection_registry.register_category("datafiles", _generic_iregistrer)
        self.isection_registry.register_category("scripts", _generic_iregistrer)

    def register_category(self, category_name, category_type="pythonfiles"):
        self.outputs_registry.register_category(category_name, category_type)
        self.isection_registry.register_category(category_name, _generic_iregistrer)

    def register_outputs(self, category_name, section_name, nodes, from_node=None, target_dir="$sitedir"):
        if from_node is None:
            from_node = self.build_node
        self.outputs_registry.register_outputs(category_name, section_name, nodes, from_node, target_dir)

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
        self.builder_registry.register_callback("extensions", full_name, builder)

    def default_builder(self, extension, **kw):
        return self.builder_registry.default_callback(
                                        "extensions",
                                        extension,
                                        **kw)

    def default_library_builder(self, library, **kw):
        return self.builder_registry.default_callback(
                                        "compiled_libraries",
                                        library,
                                        **kw)

    def disable_extension(self, extension_name):
        def nobuild(extension):
            pass
        self.register_builder(extension_name, nobuild)

    def register_compiled_library_builder(self, clib_name, builder):
        relpos = self.local_node.path_from(self.top_node)
        full_name = os.path.join(relpos, clib_name).replace(os.sep, ".")
        self.builder_registry.register_callback("compiled_libraries", full_name, builder)

    def compile(self):
        for category in ("packages", "modules", "datafiles"):
            for name, value in self._node_pkg.iter_category(category):
                builder = self.builder_registry.builder(category, name)
                name, nodes, from_node, target_dir = builder(name, value)
                self.outputs_registry.register_outputs(category, name, nodes, from_node, target_dir)

        category = "scripts"
        for name, executable in self.pkg.executables.items():
            builder = self.builder_registry.builder(category, name)
            name, nodes, from_node, target_dir = builder(name, executable)
            self.outputs_registry.register_outputs(category, name, nodes, from_node, target_dir)

        if self.pkg.config_py:
            content = _config_content(self.get_paths_scheme())
            target_node = self.build_node.make_node(self.pkg.config_py)
            target_node.parent.mkdir()
            target_node.safe_write(content)
            self.outputs_registry.register_outputs("modules", "bento_config", [target_node],
                                                   self.build_node, "$sitedir")

        if self.pkg.meta_template_file:
            target_node = write_template(self.top_node, self.pkg)
            self.outputs_registry.register_outputs("modules", "meta_from_template", [target_node],
                                                   self.build_node, "$sitedir")
    def post_compile(self):
        # Do the output_registry -> installed sections registry convertion
        section_writer = self.section_writer

        for category, name, nodes, from_node, target_dir in self.outputs_registry.iter_over_category():
            installed_category = self.outputs_registry.installed_categories[category]
            if installed_category in section_writer.sections:
                sections = section_writer.sections[installed_category]
            else:
                sections = section_writer.sections[installed_category] = {}
            registrer = self.isection_registry.registrer(category, name)
            sections[name] = registrer(installed_category, name, nodes, from_node, target_dir)

        # FIXME: this is quite stupid.
        if self.inplace:
            scheme = _compute_scheme(self.package_options)
            scheme["prefix"] = scheme["eprefix"] = self.run_node.abspath()
            scheme["sitedir"] = self.run_node.abspath()

            if self.pkg.config_py:
                target_node = self.build_node.find_node(self.pkg.config_py)
            else:
                target_node = None

            def _install_node(category, node, from_node, target_dir):
                installed_path = subst_vars(target_dir, scheme)
                target = os.path.join(installed_path, node.path_from(from_node))
                copy_installer(node.srcpath(), target, category)

            intree = (self.top_node == self.run_node)
            if intree:
                for category, name, nodes, from_node, target_dir in self.outputs_registry.iter_over_category():
                    for node in nodes:
                        if node != target_node and node.is_bld():
                            _install_node(category, node, from_node, target_dir)
            else:
                for category, name, nodes, from_node, target_dir in self.outputs_registry.iter_over_category():
                    for node in nodes:
                        if node != target_node:
                            _install_node(category, node, from_node, target_dir)

class SdistContext(CmdContext):
    def __init__(self, global_context, cmd_args, option_context, pkg, run_node):
        super(SdistContext, self).__init__(global_context, cmd_args, option_context, pkg, run_node)

        self._node_pkg = NodeRepresentation(run_node, self.top_node)
        self._node_pkg.update_package(pkg)

        if self.pkg.meta_template_file:
            output = write_template(self.top_node, pkg)
            self.register_source_node(output, output.bldpath())

    def register_source_node(self, node, archive_name=None):
        """Register a node into the source distribution.

        archive_name is an optional string which will be used for the file name
        in the archive."""
        self._node_pkg._extra_source_nodes.append(node)
        if archive_name:
            self._node_pkg._aliased_source_nodes[node] = archive_name
