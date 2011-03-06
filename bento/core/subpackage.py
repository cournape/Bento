import os

from bento.core.utils \
    import \
        resolve_glob, normalize_path
from bento.core.pkg_objects \
    import \
        Extension, CompiledLibrary

class SubPackageDescription:
    def __init__(self, rdir, packages=None, extensions=None,
                 compiled_libraries=None):
        self.rdir = rdir
        if packages is None:
            self.packages = []
        else:
            self.packages = packages
        if extensions is None:
            self.extensions = {}
        else:
            self.extensions = extensions
        if compiled_libraries is None:
            self.compiled_libraries = {}
        else:
            self.compiled_libraries = compiled_libraries

    def __repr__(self):
        return repr({"packages": self.packages,
                     "clibs": self.compiled_libraries,
                     "extensions": self.extensions})

def flatten_subpackage_packages(spkg, top_node):
    """Translate the (python) packages from a subpackage relatively to
    the given top node.
    """
    local_node = top_node.find_dir(spkg.rdir)
    parent_pkg = local_node.path_from(top_node).replace(os.pathsep, ".")
    ret = ["%s.%s" % (parent_pkg, p) for p in spkg.packages]
    return ret

def flatten_subpackage_extensions(spkg, top_node):
    """Translate the extensions from a subpackage relatively to the
    given top node.

    Extension name, source files and include directories paths are all
    translated relatively to the top node.

    Returns
    -------
    d : dict
        {ext_name: ext} dictionary

    Example
    -------
    Defining in /foo/bar the extension::

        Extension("_hello", sources=["src/hellomodule.c"])

    and top_node corresponding to /foo, the
    extension would be translated as::

        Extension("bar._hello", sources=["bar/src/hellomodule.c"])
    """
    local_node = top_node.find_dir(spkg.rdir)
    if local_node is None:
        raise IOError("Path %s not found" % \
                      os.path.join(top_node.abspath(), spkg.rdir))
    elif local_node == top_node:
        raise ValueError("Subpackage in top directory ??")

    ret = {}
    for name, extension in spkg.extensions.items():
        full_name = spkg.rdir + ".%s" % name
        sources = []
        for s in extension.sources:
            node = local_node.find_node(s)
            if node is None:
                raise IOError("File %s not found" % s)
            sources.append(node.path_from(top_node))
        include_dirs = [
                local_node.find_node(d).path_from(top_node) \
                for d in extension.include_dirs]
        ret[full_name] = Extension(full_name, sources, include_dirs)
    return ret

def flatten_subpackage_compiled_libraries(spkg, top_node):
    """Translate the compiled libraries from a subpackage relatively
    to the given top node.

    Source files and include directories paths are all
    translated relatively to the top node.

    Returns
    -------
    d : dict
        {name: clib} dictionary

    Example
    -------
    Defining in /foo/bar the compiled library::

        CompiledLibrary("fubar", sources=["src/fubar.c"])

    and top_node corresponding to /foo, the
    extension would be translated as::

        CompiledLibrary("fubar", sources=["bar/src/fubar.c"])
    """
    local_node = top_node.find_dir(spkg.rdir)
    if local_node is None:
        raise IOError("Path %s not found" % \
                      os.path.join(top_node.abspath(), spkg.rdir))
    elif local_node == top_node:
        raise ValueError("Subpackage in top directory ??")

    ret = {}
    for name, clib in spkg.compiled_libraries.items():
        sources = resolve_glob(clib.sources, local_node.abspath())
        sources = [local_node.find_node(s).path_from(top_node) \
                   for s in sources]
        include_dirs = [
                local_node.find_node(d).path_from(top_node) \
                for d in clib.include_dirs]
        full_name = normalize_path(os.path.join(spkg.rdir, name))
        ret[full_name] = CompiledLibrary(full_name, sources, include_dirs)
    return ret

def get_extensions(pkg, top_node):
    """Return the dictionary {name: extension} of all every extension
    in pkg, including the one defined in subpackages (if any).

    Note
    ----
    Extensions defined in subpackages are translated relatively to
    top_dir
    """
    extensions = {}
    for name, ext in pkg.extensions.items():
        extensions[name] = ext
    for spkg in pkg.subpackages.values():
        extensions.update(
                flatten_subpackage_extensions(spkg, top_node))
    return extensions

def get_compiled_libraries(pkg, top_node):
    """Return the dictionary {name: extension} of every compiled library in
    pkg, including the one defined in subpackages (if any).

    Note
    ----
    Extensions defined in subpackages are translated relatively to
    top_dir
    """
    libraries = {}
    for name, ext in pkg.compiled_libraries.items():
        libraries[name] = ext
    for spkg in pkg.subpackages.values():
        local_libs = flatten_subpackage_compiled_libraries(spkg,
                                                           top_node)
        libraries.update(local_libs)
    return libraries

def get_packages(pkg, top_node):
    """Return the dictionary {name: package} of every (python) package
    in pkg, including the one defined in subpackages (if any).
    """
    packages = [p for p in pkg.packages]
    for spkg in pkg.subpackages.values():
        local_pkgs = flatten_subpackage_packages(spkg, top_node)
        packages.extend(local_pkgs)
    return packages
