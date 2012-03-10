import os

import warnings

from bento.core.pkg_objects \
    import \
        Extension
from bento.core.node \
    import \
        split_path

def translate_name(name, ref_node, from_node):
    if from_node != ref_node:
        parent_pkg = ref_node.path_from(from_node).replace(os.sep, ".")
        return ".".join([parent_pkg, name])
    else:
        return name

class NodeDataFiles(object):
    def __init__(self, name, nodes, ref_node, target_dir):
        self.name = name
        self.nodes = nodes
        self.ref_node = ref_node
        self.target_dir = target_dir

class NodeExtension(object):
    def __init__(self, name, nodes, top_node, ref_node, sub_directory_node=None):
        self.name = name
        self.top_node = top_node
        self.ref_node = ref_node
        self.nodes = nodes

        if sub_directory_node is None:
            self.top_or_lib_node = top_node
        else:
            self.top_or_lib_node = sub_directory_node

        if not ref_node.is_child_of(self.top_or_lib_node):
            self.full_name = name
        else:
            self.full_name = translate_name(name, ref_node, self.top_or_lib_node)

    def extension_from(self, from_node=None):
        if len(self.nodes) < 1:
            return Extension(self.name, [])
        else:
            if from_node is None:
                from_node = self.nodes[0].srcnode
            if not from_node.is_src():
                raise ValueError("node %s is not a source directory !" % from_node.abspath())
            if not self.ref_node.is_child_of(from_node):
                raise ValueError("from_node should be a parent of %s, but is %s" % \
                                 (self.ref_node.abspath(), from_node.abspath()))
            else:
                def translate_full_name(full_name):
                    parent_pkg = from_node.path_from(self.top_node)
                    if parent_pkg == ".":
                        parent_components = []
                    else:
                        parent_components = split_path(parent_pkg)
                    full_name_components = self.full_name.split(".")
                    if not full_name_components[:len(parent_components)] == parent_components:
                        raise ValueError("Internal bug: unexpected parent/name components: %s %s" % \
                                         (parent_components, full_name_components))
                    else:
                        return ".".join(full_name_components[len(parent_components):])
                relative_name = translate_full_name(self.full_name)
                return Extension(relative_name, sources=[n.path_from(from_node) for n in self.nodes])

class NodePythonPackage(object):
    def __init__(self, name, nodes, top_node, ref_node, sub_directory_node=None):
        self.nodes = nodes
        self.top_node = top_node
        self.ref_node = ref_node

        if sub_directory_node is None:
            self.top_or_lib_node = top_node
        else:
            self.top_or_lib_node = sub_directory_node

        if not ref_node.is_child_of(self.top_or_lib_node):
            raise IOError()

        self.full_name = translate_name(name, ref_node, self.top_or_lib_node)

class NodeRepresentation(object):
    """Node-based representation of a Package content."""
    def __init__(self, run_node, top_node, sub_directory_node=None):
        self.top_node = top_node
        self.run_node = run_node
        self.sub_directory_node = sub_directory_node

        if sub_directory_node is None:
            self.top_or_sub_directory_node = top_node
        else:
            if not sub_directory_node.is_child_of(top_node):
                raise IOError("sub_directory_node %r is not a subdirectory of %s" % \
                              (sub_directory_node, top_node))
            self.top_or_sub_directory_node = sub_directory_node

        self._registry = {}
        for category in ("modules", "packages", "extensions",
                         "compiled_libraries", "datafiles"):
            self._registry[category] = {}

        self._extra_source_nodes = []
        self._aliased_source_nodes = {}

    def to_node_extension(self, extension, source_node, ref_node):
        nodes = []
        for s in extension.sources:
            _nodes = source_node.ant_glob(s)
            if len(_nodes) < 1:
                #name = translate_name(extension.name, ref_node, self.top_or_sub_directory_node)
                raise IOError("Sources glob entry %r for extension %r did not return any result" \
                              % (s, extension.name))
            else:
                nodes.extend(_nodes)
        if extension.include_dirs:
            raise NotImplementedError("include dirs translation not implemented yet")
        return NodeExtension(extension.name, nodes, self.top_node, ref_node, self.sub_directory_node)

    def _run_in_subpackage(self, pkg, func):
        for name, sub_pkg in pkg.subpackages.items():
            ref_node = self.top_node.find_node(sub_pkg.rdir)
            if ref_node is None:
                raise IOError("directory %s relative to %s not found !" % (sub_pkg.rdir,
                              self.top_node.abspath()))
            func(sub_pkg, ref_node)

    def _update_extensions(self, pkg):
        for name, extension in pkg.extensions.items():
            ref_node = self.top_node
            extension = self.to_node_extension(extension, self.top_node, ref_node)
            self._registry["extensions"][extension.full_name] = extension

        def _subpackage_extension(sub_package, ref_node):
            for name, extension in sub_package.extensions.items():
                extension = self.to_node_extension(extension, ref_node, ref_node)
                full_name = translate_name(name, ref_node, self.top_node)
                self._registry["extensions"][full_name] = extension
        self._run_in_subpackage(pkg, _subpackage_extension)

    def _update_libraries(self, pkg):
        for name, compiled_library in pkg.compiled_libraries.items():
            ref_node = self.top_node
            compiled_library = self.to_node_extension(compiled_library, self.top_node, ref_node)
            self._registry["compiled_libraries"][name] = compiled_library

        def _subpackage_compiled_libraries(sub_package, ref_node):
            for name, compiled_library in sub_package.compiled_libraries.items():
                compiled_library = self.to_node_extension(compiled_library, ref_node, ref_node)
                name = translate_name(name, ref_node, self.top_node)
                self._registry["compiled_libraries"][name] = compiled_library
        self._run_in_subpackage(pkg, _subpackage_compiled_libraries)

    def _update_py_packages(self, pkg):
        def _resolve_package(package_name, ref_node):
            init = os.path.join(*(package_name.split(".") + ["__init__.py"]))
            n = ref_node.find_node(init)
            if n is None:
                raise IOError("init file for package %s not found (looked for %r)!" \
                              % (package_name, init))
            else:
                p = n.parent
                nodes = [p.find_node(f) for f in p.listdir() if f.endswith(".py")]
                node_package = NodePythonPackage(package_name, nodes, self.top_node,
                                                 ref_node, self.sub_directory_node)
                self._registry["packages"][node_package.full_name] = node_package

        def _subpackage_resolve_package(sub_package, ref_node):
            for package in sub_package.packages:
                _resolve_package(package, ref_node)

        for package in pkg.packages:
            _resolve_package(package, self.top_or_sub_directory_node)
        self._run_in_subpackage(pkg, _subpackage_resolve_package)

    def _update_data_files(self, pkg):
        for name, data_section in pkg.data_files.items():
            ref_node = self.top_node.find_node(data_section.source_dir)
            nodes = []
            for f in data_section.files:
                ns = ref_node.ant_glob(f)
                if len(ns) < 1:
                    raise IOError("File/glob %s could not be resolved (data file section %s)" % (f, name))
                else:
                    nodes.extend(ns)
            self._registry["datafiles"][name] = NodeDataFiles(name, nodes, ref_node, data_section.target_dir)

    def _update_py_modules(self, pkg):
        for m in pkg.py_modules:
            n = self.top_or_sub_directory_node.find_node("%s.py" % m)
            if n is None:
                raise IOError("file for module %s not found" % m)
            else:
                self._registry["modules"][m] = n

    def _update_extra_sources(self, pkg):
        for s in pkg.extra_source_files:
            nodes = self.top_node.ant_glob(s)
            if len(nodes) < 1:
                warnings.warn("extra source files glob entry %r did not return any result" % (s,))
            self._extra_source_nodes.extend(nodes)

    def update_package(self, pkg):
        self._update_py_packages(pkg)
        self._update_py_modules(pkg)

        self._update_extensions(pkg)
        self._update_libraries(pkg)

        self._update_data_files(pkg)
        self._update_extra_sources(pkg)

    def iter_category(self, category):
        if category in self._registry:
            return self._registry[category].items()
        else:
            raise ValueError("Unknown category %s" % category)

    def register_entity(self, category, name, entity):
        if category in self._registry:
            self._registry[category][name] = entity
        else:
            raise ValueError("Category %r not registered" % category)

    def iter_source_nodes(self):
        for n in self._extra_source_nodes:
            yield n

        for d in self._registry["datafiles"].values():
            for n in d.nodes:
                yield n

        for m in self._registry["modules"].values():
            yield m
        for package in self._registry["packages"].values():
            for n in package.nodes:
                yield n

        for extension in self._registry["extensions"].values():
            for n in extension.nodes:
                yield n
        for compiled_library in self._registry["compiled_libraries"].values():
            for n in compiled_library.nodes:
                yield n

    def iter_source_files(self):
        for n in self.iter_source_nodes():
            filename = n.path_from(self.run_node)
            alias = self._aliased_source_nodes.get(n, filename)
            yield filename, alias
