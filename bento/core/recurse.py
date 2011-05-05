import os

from bento.core.pkg_objects \
    import \
        Extension

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
    def __init__(self, name, nodes, ref_node):
        self.name = name
        self.nodes = nodes
        self.ref_node = ref_node

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
                name = translate_name(self.name, self.ref_node, from_node)
                return Extension(name, sources=[n.path_from(from_node) for n in self.nodes])

def to_node_extension(extension, ref_node):
    nodes = []
    for s in extension.sources:
        n = ref_node.find_node(s)
        if n is None:
            raise IOError("file %s" % s)
        else:
            nodes.append(n)
    if extension.include_dirs:
        raise NotImplementedError("include dirs translation not implemented yet")
    return NodeExtension(extension.name, nodes, ref_node)

class NodeRepresentation(object):
    """Node-based representation of a Package content."""
    def __init__(self, top_node, source_dir):
        # top_node is process cwd, source_dir the top source directory node
        self.top_node = top_node
        self.source_dir = source_dir

        # FIXME: would make more sense to organize those as a trees to easily
        # find all the objects at different levels
        self._extensions = {}
        self._compiled_libraries = {}

        self._py_packages = {}
        self._py_modules = {}
        self._data = {}

        self._extra_source_nodes = []

    def _run_in_subpackage(self, pkg, func):
        for name, sub_pkg in pkg.subpackages.iteritems():
            ref_node = self.source_dir.find_node(sub_pkg.rdir)
            if ref_node is None:
                raise IOError("directory %s relative to %s not found !" % (sub_pkg.rdir,
                              self.source_dir.abspath()))
            func(sub_pkg, ref_node)

    def _update_extensions(self, pkg):
        for name, extension in pkg.extensions.iteritems():
            extension = to_node_extension(extension, self.source_dir)
            self._extensions[name] = extension

        def _subpackage_extension(sub_package, ref_node):
            for name, extension in sub_package.extensions.iteritems():
                extension = to_node_extension(extension, ref_node)
                name = translate_name(name, ref_node, self.source_dir)
                self._extensions[name] = extension
        self._run_in_subpackage(pkg, _subpackage_extension)

    def _update_libraries(self, pkg):
        for name, compiled_library in pkg.compiled_libraries.iteritems():
            compiled_library = to_node_extension(compiled_library, self.source_dir)
            self._compiled_libraries[name] = compiled_library

        def _subpackage_compiled_libraries(sub_package, ref_node):
            for name, compiled_library in sub_package.compiled_libraries.iteritems():
                compiled_library = to_node_extension(compiled_library, ref_node)
                name = translate_name(name, ref_node, self.source_dir)
                self._compiled_libraries[name] = compiled_library
        self._run_in_subpackage(pkg, _subpackage_compiled_libraries)

    def _update_py_packages(self, pkg):
        def _resolve_package(package, ref_node):
            init = os.path.join(*(package.split(".") + ["__init__.py"]))
            n = ref_node.find_node(init)
            if n is None:
                raise IOError("init file for package %s not found !" % package)
            else:
                p = n.parent
                self._py_packages[package] = [p.find_node(f) for f in p.listdir() if f.endswith(".py")]
        def _subpackage_resolve_package(sub_package, ref_node):
            for package in sub_package.packages:
                _resolve_package(package, ref_node)

        src = self.source_dir
        for package in pkg.packages:
            _resolve_package(package, src)
        self._run_in_subpackage(pkg, _subpackage_resolve_package)

    def _update_data_files(self, pkg):
        for name, data_section in pkg.data_files.iteritems():
            ref_node = self.source_dir.find_node(data_section.source_dir)
            nodes = []
            for f in data_section.files:
                ns = ref_node.ant_glob(f)
                if len(ns) < 1:
                    raise IOError("File/glob %s could not be resolved (data file section %s)" % (f, name))
                else:
                    nodes.extend(ns)
            self._data[name] = NodeDataFiles(name, nodes, ref_node, data_section.target_dir)

    def _update_py_modules(self, pkg):
        for m in pkg.py_modules:
            n = self.source_dir.find_node("%s.py" % m)
            if n is None:
                raise IOError("file for module %s not found" % m)
            else:
                self._py_modules[m] = n

    def _update_extra_sources(self, pkg):
        for s in pkg.extra_source_files:
            nodes = self.source_dir.ant_glob(s)
            self._extra_source_nodes.extend(nodes)

    def update_package(self, pkg):
        self._update_py_packages(pkg)
        self._update_py_modules(pkg)

        self._update_extensions(pkg)
        self._update_libraries(pkg)

        self._update_data_files(pkg)
        self._update_extra_sources(pkg)

    def iter_category(self, category):
        cat = {"extensions": self._extensions.iteritems(),
               "libraries": self._compiled_libraries.iteritems(),
               "packages": self._py_packages.iteritems(),
               "modules": self._py_modules.iteritems(),
               "datafiles": self._data.iteritems()}
        if category in cat:
            return cat[category]
        else:
            raise ValueError("Unknown category %s" % category)

    def nodes_iter(self):
        for n in self._py_modules:
            yield n
        for p in self._py_packages.itervalues():
            for n in p:
                yield n
        for extension in self._extensions.itervalues():
            for n in extension.nodes:
                yield n
        for library in self._compiled_libraries.itervalues():
            for n in library.nodes:
                yield n
        for data in self._data.itervalues():
            for n in data.nodes:
                yield n
        for n in self._extra_source_nodes:
            yield n
