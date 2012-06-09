from bento.errors \
    import \
        InvalidPackage
from bento.core.meta \
    import \
        _METADATA_FIELDS

def extract_top_dicts(d):
    """Given an "abstract" dictionary returned by parse_to_dict, build
    meta, library, options and misc dictionaries."""
    meta = {}
    misc = {"extra_source_files": [],
            "executables": {},
            "data_files": {},
            "hook_files": [],
            "config_py": None,
            "meta_template_files": [],
            "flag_options": [],
            "path_options": [],
            "subento": [],
            "use_backends": []}
    options = {}

    for k in _METADATA_FIELDS:
        if k in d:
            meta[k] = d.pop(k)
    if "libraries" in d:
        libraries = d.pop("libraries")
    else:
        libraries = {}
    for k in misc.keys():
        if k in d:
            misc[k] = d.pop(k)

    if len(d) > 0:
        raise ValueError("Unknown entry(ies) %s" % d.keys())

    return meta, libraries, options, misc

def extract_top_dicts_subento(d):
    """Given an "abstract" dictionary returned by parse_to_dict, build
    library, and misc dictionaries.
    
    This function should be used for subentos"""
    misc = {"subento": [], "hook_files": []}

    if "libraries" in d:
        libraries = d.pop("libraries")
    else:
        libraries = {}
    # FIXME: bento vs subento visitor. Those should not be defined in the first
    # place for subento.
    for library in libraries.values():
        for k, field_name in [("install_requires", "InstallRequires"), ("py_modules", "Modules")]:
            v = library.pop(k)
            if len(v) > 0:
                raise InvalidPackage("Invalid entry %r in recursed bento file(s)" % field_name)
    for k in misc.keys():
        if k in d:
            misc[k] = d.pop(k)

    # FIXME: bento vs subento visitor. Those should not be defined in the first
    # place for subento.
    for k in ["path_options", "flag_options", "data_files", "extra_source_files", "executables"]:
        v = d.pop(k)
        if len(v) > 0:
            raise ValueError("Invalid non empty entry %s" % k)
    if len(d) > 0:
        raise ValueError("Unknown entry(ies) %s" % d.keys())

    return libraries, misc
