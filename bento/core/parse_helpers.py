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
            "flag_options": [],
            "path_options": [],
            "subento": []}
    options = {}

    for k in _METADATA_FIELDS:
        if d.has_key(k):
            meta[k] = d.pop(k)
    if d.has_key("libraries"):
        libraries = d.pop("libraries")
    else:
        libraries = {}
    for k in misc.keys():
        if d.has_key(k):
            misc[k] = d.pop(k)

    if len(d) > 0:
        raise ValueError("Unknown entry(ies) %s" % d.keys())

    return meta, libraries, options, misc

def extract_top_dicts_subento(d):
    """Given an "abstract" dictionary returned by parse_to_dict, build
    library, and misc dictionaries.
    
    This function should be used for subentos"""
    misc = {"subento": []}

    if d.has_key("libraries"):
        libraries = d.pop("libraries")
    else:
        libraries = {}
    for k in misc.keys():
        if d.has_key(k):
            misc[k] = d.pop(k)

    if len(d) > 0:
        raise ValueError("Unknown entry(ies) %s" % d.keys())

    return libraries, misc
