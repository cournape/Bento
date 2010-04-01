import os

from toydist.core.reader import \
        Reader
from toydist.core.utils import \
    subst_vars
from toydist.core.pkg_objects import \
    Executable

META_DELIM = "!- FILELIST"
FIELD_DELIM = ("\t", " ")

class InstalledSection(object):
    @classmethod
    def from_data_files(cls, name, data_files):
        return cls("datafiles", name,
                   data_files.source_dir,
                   data_files.target_dir,
                   data_files.files)
        
    def __init__(self, tp, name, srcdir, target, files):
        self.tp = tp
        self.name = name
        self.srcdir = srcdir
        self.target = target
        self.files = files

    @property
    def fullname(self):
        return self.tp + ":" + self.name

    def write_section(self, fid):
        if len(self.files) > 0:
            fid.write(write_file_section(self.fullname, self.srcdir,
                                         self.target, self.files))

def iter_source_files(file_sections):
    for kind in file_sections:
        if not kind in ["executables"]:
            for name, section in file_sections[kind].items():
                for f in section:
                    yield f[0]

def iter_files(file_sections):
    for kind in file_sections:
        for name, section in file_sections[kind].items():
            for source, target in section:
                yield kind, source, target

class InstalledPkgDescription(object):
    @classmethod
    def from_file(cls, filename):
        f = open(filename)
        try:
            vars = []
            r = Reader(f.readlines())

            meta_vars = {}
            meta_vars["description"] = []
            meta_vars["classifiers"] = []
            meta_vars["platforms"] = []
            meta_vars["install_requires"] = []
            meta_vars["top_levels"] = []
            while r.wait_for("!- VARIABLES\n"):
                line = r.pop().strip()
                k, v = line.split("=", 1)
                if k in ["description", "classifiers", "platforms",
                         "install_requires", "top_levels"]:
                    meta_vars[k].append(v)
                else:
                    meta_vars[k] = v

            if r.eof():
                r.parse_error("Missing variables section")
            r.pop()
            meta_vars["description"] = "\n".join(meta_vars["description"])

            def read_var_section(section_name):
                r.flush_empty()
                line = r.peek()
                if line and line[0] in FIELD_DELIM:
                    r.parse_error("No section found ?")
                line = r.pop()
                if section_name != line.strip():
                    r.parse_error("Expected section %s, got %s" % section_name, line.strip())

                fields = []
                line = r.peek()
                while line and line[0] in FIELD_DELIM:
                    fields.append(r.pop().strip())
                    line = r.peek()

                return fields

            vars = read_var_section("paths")
            path_vars = {}
            for i in vars:
                name, value = [j.strip() for j in i.split("=")]
                path_vars[name] = value

            vars = read_var_section("executables")
            executables = {}
            for var in vars:
                exe = Executable.from_representation(var)
                executables[exe.name] = exe

            if r.eof():
                r.parse_error("Missing filelist section")
            r.pop()

            def read_section():
                r.flush_empty()
                line = r.peek()
                if line and line[0] in FIELD_DELIM:
                    r.parse_error("No section found ?")
                line = r.pop()
                type, section_name = line.strip().split(":", 1)

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

                return type, section_name, {'files': files, 'srcdir': srcdir, 'target': target}

            file_sections = {}
            while not r.eof():
                type, name, files = read_section()
                if type in file_sections:
                    if name in file_sections[type]:
                        raise ValueError("section %s of type %s already exists !" % (name, type))
                    file_sections[type][name] = files
                else:
                    file_sections[type] = {name: files}

            return cls(file_sections, meta_vars, path_vars, executables)
        finally:
            f.close()

    def __init__(self, files, meta, path_options, executables):
        self.files = files
        self.meta = meta
        self.path_variables = path_options
        self.executables = executables

    def write(self, filename):
        fid = open(filename, "w")
        try:
            meta = []
            for k, v in self.meta.items():
                if k == "description" and v is not None:
                    for line in v.splitlines():
                        meta.append("description=%s" % line)
                elif k in ["classifiers", "platforms", "install_requires", "top_levels"]:
                    for i in v:
                        meta.append("%s=%s" % (k, i))
                elif k == "console_scripts":
                    raise ValueError("Using console_scripts is not supported anymore")
                else:
                    meta.append("%s=%s" % (k, v))

            fid.write("\n".join(meta))
            fid.write("\n!- VARIABLES\n")

            path_fields = "\n".join([
                "\t%s=%s" % (name, value) for name, value in
                                              self.path_variables.items()])

            path_section = """\
paths
%s
""" % path_fields
            fid.write(path_section)

            executables_fields = "\n".join(["\t%s=%s" % \
                                            (name, value.representation()) 
                                            for name, value in 
                                                self.executables.items()])
            executables_section = """\
executables
%s
""" % executables_fields
            fid.write(executables_section)
            fid.write(META_DELIM + "\n")

            for type, value in self.files.items():
                if type in ["pythonfiles"]:
                    for i in value.values():
                        i.srcdir = "$_srcrootdir"
                        i.write_section(fid)
                elif type in ["datafiles", "extension", "executable"]:
                    for i in value.values():
                        i.write_section(fid)
                else:
                    raise ValueError("Unknown section %s" % type)

        finally:
            fid.close()

    def resolve_paths(self, src_root_dir="."):
        self.path_variables['_srcrootdir'] = src_root_dir

        file_sections = {}
        for tp in self.files:
            file_sections[tp] = {}
            for name, value in self.files[tp].items():
                srcdir = subst_vars(value["srcdir"], self.path_variables)
                target = subst_vars(value["target"], self.path_variables)

                file_sections[tp][name] = \
                        [(os.path.join(srcdir, f), os.path.join(target, f))
                         for f in value["files"]]

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
