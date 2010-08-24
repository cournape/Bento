from bento.core.pkg_objects \
    import \
        Extension

def flatten_subpackage_extensions(spkg, top_node):
    """Translate the extensions from a subpackage relatively to the
    given top node.

    Extension name, source files and include directories paths are all
    translated relatively to the top node.
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
        sources = [local_node.find_node(s).path_from(top_node) \
                   for s in extension.sources]
        include_dirs = [
                local_node.find_node(d).path_from(top_node) \
                for d in extension.include_dirs]
        ret[full_name] = Extension(full_name, sources, include_dirs)
    return ret
