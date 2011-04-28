import os

from bento.core.pkg_objects \
    import \
        Extension, CompiledLibrary

def translate_name(name, ref_node, from_node):
    if from_node != ref_node:
        parent_pkg = ref_node.path_from(from_node).replace(os.sep, ".")
        return ".".join([parent_pkg, name])
    else:
        return name

class NodeExtension(object):
    def __init__(self, name, nodes, ref_node):
        self.name = name
        self.nodes = nodes
        self.ref_node = ref_node

    def extension_from(self, from_node=None):
        if len(self.nodes) < 1:
            return Extension(name, [])
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
    def __init__(self, top_node, srcdir_node):
        # top_node is process cwd, srcdir_node the top source directory node
        self.top_node = top_node
        self.srcdir_node = srcdir_node

        # FIXME: would make more sense to organize those as a trees to easily
        # find all the objects at different levels
        self._extensions = {}
        self._compiled_libraries = {}

    def update_package(self, pkg):
        for name, extension in pkg.extensions.iteritems():
            extension = to_node_extension(extension, self.srcdir_node)
            self._extensions[name] = extension
        for name, library in pkg.compiled_libraries.iteritems():
            library = to_node_extension(library, self.srcdir_node)
            self._compiled_libraries[name] = library

        for name, sub_pkg in pkg.subpackages.iteritems():
            ref_node = self.srcdir_node.find_node(sub_pkg.rdir)
            if ref_node is None:
                raise IOError("directory %s relative to %s not found !" % (sub_pkg.rdir,
                              self.srcdir_node.abspath()))
            for name, extension in sub_pkg.extensions.iteritems():
                extension = to_node_extension(extension, ref_node)
                name = translate_name(name, ref_node, self.srcdir_node)
                self._extensions[name] = extension
            for name, library in sub_pkg.compiled_libraries.iteritems():
                library = to_node_extension(library, ref_node)
                name = translate_name(name, ref_node, self.srcdir_node)
                self._compiled_libraries[name] = library
