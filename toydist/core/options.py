from toydist.cabal_parser.cabal_parser import \
        parse

class PackageOptions(object):
    @classmethod
    def __from_data(cls, data):
        d = parse(data)

        kw = {}
        if not "name" in d:
            raise ValueError("No name field found")
        kw["name"] = d["name"]

        for k in ["path_options", "flag_options"]:
            if d.has_key(k):
                kw[k] = d[k]

        return cls(**kw)

    @classmethod
    def from_file(cls, filename):
        """Create a PackageOptions instance from a toysetup.info file."""
        fid = open(filename, 'r')
        try:
            data = fid.readlines()
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
            self.flag_options = flags_options
