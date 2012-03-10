import os
import sys
import copy
import warnings

from bento.compat.api import json
import bento.compat.api as compat

from bento.core.node \
    import \
        find_root
from bento.core.platforms \
    import \
        get_scheme
from bento.core.utils \
    import \
        subst_vars, normalize_path, unnormalize_path, same_content, fix_kw, \
        explode_path
from bento.core.pkg_objects \
    import \
        Executable

def ipkg_meta_from_pkg(pkg):
    """Return meta dict for Installed pkg from a PackageDescription
    instance."""
    meta = {}
    for m in ["name", "version", "summary", "url", "author",
              "author_email", "license", "download_url", "description",
              "platforms", "classifiers", "install_requires", 
              "top_levels"]:
        meta[m] = getattr(pkg, m)
    return meta

class InstalledSection(object):
    @classmethod
    def from_source_target_directories(cls, category, name, source_dir, target_dir, files):
        files = [(f, f) for f in files]
        return cls(category, name, source_dir, target_dir, files)

    def __init__(self, category, name, srcdir, target, files):
        self.category = category
        self.name = name
        if os.sep != "/":
            self.source_dir = normalize_path(srcdir)
            self.target_dir = normalize_path(target)
            self.files = [(normalize_path(f), normalize_path(g)) for f, g in files]
        else:
            self.source_dir = srcdir
            self.target_dir = target
            self.files = files

    def __repr__(self):
        ret = """\
InstalledSection(%(category)s,
    %(name)s,
    %(source_dir)s,
    %(target_dir)s,
    %(files)s)""" % {"name": self.name, "category": self.category,
            "source_dir": self.source_dir, "target_dir": self.target_dir,
            "files": self.files}
        return ret

    def __eq__(self, other):
        return self.category == other.category and \
                self.name == other.name and \
                self.source_dir == other.source_dir and \
                self.target_dir == other.target_dir and \
                self.files == other.files

def iter_source_files(file_sections):
    for kind in file_sections:
        if not kind in ["executables"]:
            for name, section in file_sections[kind].items():
                for f in section:
                    yield f[0]

def iter_files(file_sections):
    # XXX: what to do with multiple source for a same target ? It is not always
    # easy to avoid this situation, especially for python files and files
    # installed from wildcards. For now, we raise an exception unless the
    # sources have the exact same content, but this may not be enough (what if
    # category changes ? This may cause different target permissions and other
    # category-specific post-processing during install)
    installed_files = {}
    def _is_redundant(source, target):
        source_path = source.abspath()
        target_path = target.abspath()
        # If this install already installs something @ target, we raise an
        # error unless the content is exactly the same
        if not target_path in installed_files:
            installed_files[target_path] = source_path
            return False
        else:
            if not same_content(source_path, installed_files[target_path]):
                raise IOError("Multiple source_path for same target_path %r !" % target_path)
            else:
                return True

    for kind in file_sections:
        for name, section in file_sections[kind].items():
            for source, target in section:
                if not _is_redundant(source, target):
                    yield kind, source, target

class InstalledPkgDescription(object):
    @classmethod
    def from_egg(cls, egg_path):
        zid = compat.ZipFile(egg_path)
        try:
            data = json.loads(zid.read("EGG-INFO/ipkg.info"))
            return cls.from_json_dict(data)
        finally:
            zid.close()

    @classmethod
    def from_json_dict(cls, d):
        return cls.__from_data(d)

    @classmethod
    def from_string(cls, s):
        return cls.__from_data(json.loads(s))

    @classmethod
    def from_file(cls, filename):
        fid = open(filename)
        try:
            return cls.__from_data(json.load(fid))
        finally:
            fid.close()

    @classmethod
    def __from_data(cls, data):
        meta_vars = fix_kw(data["meta"])
        #variables = data["variables"]
        install_paths = data.get("install_paths", None)

        executables = {}
        for name, executable in data["executables"].items():
            executables[name] = Executable.from_parse_dict(fix_kw(executable))

        file_sections = {}

        def json_to_file_section(data):
            category = data["category"]
            name = data["name"]
            section = InstalledSection(category, name, data["source_dir"],
                                       data["target_dir"], data["files"])
            return category, name, section

        for section in data["file_sections"]:
            category, name, files = json_to_file_section(section)
            if category in file_sections:
                if name in file_sections[category]:
                    raise ValueError("section %s of type %s already exists !" % (name, category))
                file_sections[category][name] = files
            else:
                file_sections[category] = {name: files}
        return cls(file_sections, meta_vars, executables, install_paths)

    def __init__(self, files, meta, executables, path_variables=None):
        self.files = files
        self.meta = meta
        if path_variables is None:
            self._path_variables = get_scheme(sys.platform)[0]
        else:
            self._path_variables = path_variables
        self.executables = executables

        self._variables = {"pkgname": self.meta["name"],
                           "py_version_short": ".".join([str(i) for i in sys.version_info[:2]])}

    def write(self, filename):
        fid = open(filename, "w")
        try:
            return self._write(fid)
        finally:
            fid.close()

    def _write(self, fid):
        def executable_to_json(executable):
            return {"name": executable.name,
                    "module": executable.module,
                    "function": executable.function}

        def section_to_json(section):
            return {"name": section.name,
                    "category": section.category,
                    "source_dir": section.source_dir,
                    "target_dir": section.target_dir,
                    "files": section.files}

        data = {}
        data["meta"] = self.meta

        executables = dict([(k, executable_to_json(v)) \
                            for k, v in self.executables.items()])
        data["executables"] = executables
        data["install_paths"] = self._path_variables

        file_sections = []
        for category, value in self.files.items():
            if category in ["pythonfiles", "bentofiles"]:
                for i in value.values():
                    i.srcdir = "$_srcrootdir"
                    file_sections.append(section_to_json(i))
            elif category in ["datafiles", "extensions", "executables",
                        "compiled_libraries"]:
                for i in value.values():
                    file_sections.append(section_to_json(i))
            else:
                warnings.warn("Unknown category %r" % category)
                for i in value.values():
                    file_sections.append(section_to_json(i))
        data["file_sections"] = file_sections
        if "BENTOMAKER_PRETTY" in os.environ:
            json.dump(data, fid, sort_keys=True, indent=4)
        else:
            json.dump(data, fid, separators=(',', ':'))

    def update_paths(self, paths):
        for k, v in paths.items():
            self._path_variables[k] = v

    def resolve_path(self, path):
        variables = copy.copy(self._path_variables)
        variables.update(self._variables)
        return subst_vars(path, variables)

    def resolve_paths_with_destdir(self, src_root_node):
        """Same as resolve_paths, but prefix every path with $destdir."""
        return self._resolve_paths(src_root_node, use_destdir=True)

    def resolve_paths(self, src_root_node):
        return self._resolve_paths(src_root_node, use_destdir=False)

    def _resolve_paths(self, src_root_node, use_destdir):
        variables = copy.copy(self._path_variables)
        variables.update(self._variables)
        variables['_srcrootdir'] = src_root_node.abspath()

        root = find_root(src_root_node)

        def _prefix_destdir(path):
            destdir = subst_vars("$destdir", variables)
            if path:
                tail = explode_path(path)[1:]
                if not tail:
                    raise ValueError("Invalid target directory in section %r "
                                     "(not absolute: %r)" % (name, path))
                return os.path.join(destdir, os.path.join(*tail))
            else:
                raise ValueError("Invalid target directory in section "
                                 "%r: %r" % (name, path))

        node_sections = {}
        for category in self.files:
            node_sections[category] = {}
            for name, section in self.files[category].items():
                srcdir = subst_vars(section.source_dir, variables)
                target = subst_vars(section.target_dir, variables)

                if use_destdir:
                    target = _prefix_destdir(target)

                srcdir_node = root.find_node(srcdir)
                if srcdir_node is None:
                    raise IOError("directory %r not found !" % (srcdir,))
                target_node = root.make_node(target)
                node_sections[category][name] = \
                        [(srcdir_node.find_node(f), target_node.make_node(g))
                         for f, g in section.files]

        return node_sections
