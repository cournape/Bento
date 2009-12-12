import shutil
import os

from toydist.utils import \
    subst_vars
from toydist.cabal_parser.cabal_parser import \
    ParseError

META_DELIM = "!- FILELIST"
FIELD_DELIM = ("\t", " ")

class InstalledPkgDescription(object):
    @classmethod
    def from_file(cls, filename):
        f = open(filename)
        try:
            vars = []
            meta = []
            r = Reader(f.readlines())

            meta_vars = {}
            meta_vars["description"] = []
            meta_vars["classifiers"] = []
            while r.wait_for("!- VARIABLES\n"):
                line = r.pop().strip()
                k, v = line.split("=", 1)
                if k in ["description", "classifiers"]:
                    meta_vars[k].append(v)
                else:
                    meta_vars[k] = v

            if r.eof():
                r.parse_error("Missing variables section")
            r.pop()
            meta_vars["description"] = "\n".join(meta_vars["description"])

            while r.wait_for("!- FILELIST\n"):
                vars.append(r.pop())
            if r.eof():
                r.parse_error("Missing filelist section")
            r.pop()

            if not vars[0].strip() == "paths":
                raise ValueError("no path ?")

            path_vars = {}
            for i in vars[1:]:
                name, value = [j.strip() for j in i.split("=")]
                path_vars[name] = value

            def read_section():
                r.flush_empty()
                line = r.peek()
                if line and line[0] in FIELD_DELIM:
                    r.parse_error("No section found ?")
                line = r.pop()
                section_name = line.strip()

                srcdir = r.pop().strip()
                target = r.pop().strip()
                assert srcdir.startswith("srcdir=")
                assert target.startswith("target=")
                srcdir = srcdir.split("=")[1]
                target = target.split("=")[1]

                files = []
                line = r.peek()
                while line and line[0] in FIELD_DELIM:
                    files.append(r.pop().strip())
                    line = r.peek()

                return section_name, {'files': files, 'srcdir': srcdir, 'target': target}

            file_sections = {}
            while not r.eof():
                name, files = read_section()
                file_sections[name] = files

            return cls(file_sections, path_vars, meta_vars)
        finally:
            f.close()

    def __init__(self, files, path_options, meta):
        self.files = files
        self._meta = meta
        self._path_variables = path_options

    def write(self, filename):
        fid = open(filename, "w")
        try:
            meta = []
            for k, v in self._meta.items():
                if k == "description":
                    for line in v.splitlines():
                        meta.append("description=%s" % line)
                elif k in ["classifiers", "platforms"]:
                    for i in v:
                        meta.append("%s=%s" % (k, i))
                else:
                    meta.append("%s=%s" % (k, v))

            fid.write("\n".join(meta))
            fid.write("\n!- VARIABLES\n")

            path_fields = "\n".join([
                "\t%s=%s" % (name, value) for name, value in
                                              self._path_variables.items()])

            path_section = """\
paths
%s
%s
""" % (path_fields, META_DELIM)
            fid.write(path_section)

            for name, value in self.files.items():
                if name in ["pythonfiles"]:
                    srcdir = "$_srcrootdir"
                    target = value["target"]
                    files = value["files"]
                    fid.write(write_file_section(name, srcdir, target, files))
                elif name in ["datafiles"]:
                    for dname, dvalue in self.files["datafiles"].items():
                        srcdir = dvalue["srcdir"]
                        target = dvalue["target"]
                        files = dvalue["files"]
                        fid.write(write_file_section(dname, srcdir, target, files))
                elif name in ["extensions"]:
                    for ename, evalue in self.files["extensions"].items():
                        srcdir = evalue["srcdir"]
                        target = evalue["target"]
                        files = evalue["files"]
                        fid.write(write_file_section(ename, srcdir, target, files))
                else:
                    raise ValueError("Unknown section %s" % name)

        finally:
            fid.close()

    def resolve_paths(self, src_root_dir="."):
        self._path_variables['_srcrootdir'] = src_root_dir

        file_sections = {}
        for name, value in self.files.items():
            srcdir = value["srcdir"]
            target = value["target"]

            srcdir = subst_vars(srcdir, self._path_variables)
            target = subst_vars(target, self._path_variables)

            files = [(os.path.join(srcdir, file), os.path.join(target, file))
                     for file in value["files"]]
            file_sections[name] = files

        return file_sections 

def write_file_section(name, srcdir, target, files):
    section = """\
%(section)s
%(srcdir)s
%(target)s
%(files)s
""" % {"section": name,
       "srcdir": "\tsrcdir=%s" % srcdir,
       "target": "\ttarget=%s" % target,
       "files": "\n".join(["\t%s" % f for f in files])}
    return section

# XXX: abstract this with the reader in cabal_parser
class Reader(object):
    def __init__(self, data):
        self._data = data
        self._idx = 0

    def flush_empty(self):
        """Read until a non-empty line is found."""
        while not (self.eof() or self._data[self._idx].strip()):
            self._idx += 1

    def pop(self, blank=False):
        """Return the next non-empty line and increment the line
        counter.  If `blank` is True, then also return blank lines.

        """
        if not blank:
            # Skip to the next non-empty line if blank is not set
            self.flush_empty()

        line = self.peek(blank)
        self._idx += 1

        return line

    def peek(self, blank=False):
        """Return the next non-empty line without incrementing the
        line counter.  If `blank` is True, also return blank lines.

        Peek is not allowed to touch _idx.

        """
        if self.eof():
            return ''

        save_idx = self._idx
        if not blank:
            self.flush_empty()

        peek_line = self._data[self._idx]
        self._idx = save_idx

        return peek_line

    def eof(self):
        """Return True if the end of the file has been reached."""
        return self._idx >= len(self._data)

    @property
    def index(self):
        """Return the line-counter to the pre-processed version of
        the input file.

        """
        return self._idx

    @property
    def line(self):
        """Return the line-counter to the original input file.

        """
        lines = 0
        for l in self._data[:self._idx]:
            if not l in ['{', '}']:
                lines += 1
        return lines

    def wait_for(self, line):
        """Keep reading until the given line has been seen."""
        if self.eof():
            return False
        elif self.peek() != line:
            return True
        else:
            return False

    def parse_error(self, msg):
        """Raise a parsing error with the given message."""
        raise ParseError('''

Parsing error at line %s (%s):
%s
Parser traceback: %s''' %
                         (self.line, msg, self._original_data[self.line],
                          ' -> '.join(self._traceback)))

