from toydist.cabal_parser.utils import \
    comma_list_split
from toydist.utils import \
    expand_glob

class DataFiles(object):
    @classmethod
    def from_parse_dict(cls, name, d):
        kw = {}
        kw["target"] = d["target"]
        kw["srcdir"] = d.get("srcdir", None)
        kw["files"] = d.get('files', None)
        if kw["files"]:
            kw["files"] = comma_list_split(kw['files'])

        return cls(name=name, **kw)

    def __init__(self, name, files=None, target=None, srcdir=None):
        self.name = name

        if files is not None:
            self.files = files
        else:
            self.files = []

        if target is not None:
            self.target = target
        else:
            self.target = "$sitedir"

        if srcdir is not None:
            self.srcdir = srcdir
        else:
            self.srcdir = "."

    def resolve_glob(self):
        """Expand any glob pattern in the files section relatively to the
        current value for source direcory."""
        files = []
        for f in self.files:
            files.extend(expand_glob(f, self.srcdir))
        return files

    def __repr__(self):
        return repr({"files": self.files, "srcdir": self.srcdir, "target": self.target})

