from bento.core.parser.api \
    import \
        raw_parse, build_ast_from_raw_dict
from bento.core.pkg_objects \
    import \
        PathOption, FlagOption

def raw_to_options_kw(raw):
    d = build_ast_from_raw_dict(raw)

    kw = {}
    if not "name" in d:
        raise ValueError("No name field found")
    kw["name"] = d["name"]

    kw["path_options"] = {}
    path_options = d.get("path_options", {})
    for name, path in path_options.items():
        kw["path_options"][name] = PathOption(path["name"],
                                              path["default"],
                                              path["description"])

    kw["flag_options"] = {}
    flag_options = d.get("flag_options", {})
    for name, flag in flag_options.items():
        kw["flag_options"][name] = FlagOption(flag["name"],
                                              flag["default"],
                                              flag["description"])

    return kw

class PackageOptions(object):
    @classmethod
    def __from_data(cls, data):
        raw = raw_parse(data)
        kw = raw_to_options_kw(raw)
        return cls(**kw)

    @classmethod
    def from_string(cls, str):
        """Create a PackageOptions instance from a bento.info content."""
        return cls.__from_data(str)

    @classmethod
    def from_file(cls, filename):
        """Create a PackageOptions instance from a bento.info file."""
        fid = open(filename, 'r')
        try:
            data = fid.read()
            return cls.__from_data(data)
        finally:
            fid.close()

    def __init__(self, name, path_options=None, flag_options=None):
        """Create a PackageOptions instance

        Parameters
        ----------
        name: str
            name of the package
        path_options: dict
            dict of path options
        flag_options: dict
            dict of flag options
        """
        self.name = name

        if not path_options:
            self.path_options = {}
        else:
            self.path_options = path_options

        if not flag_options:
            self.flag_options = {}
        else:
            self.flag_options = flag_options
