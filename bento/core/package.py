import os
import warnings

from copy \
    import \
        deepcopy

from bento.core.pkg_objects \
    import \
        Extension, DataFiles, Executable, CompiledLibrary
from bento.core.meta \
    import \
        _set_metadata, _METADATA_FIELDS
from bento.core.utils \
    import \
        unnormalize_path
from bento.core.parser.api \
    import \
        build_ast_from_raw_dict, raw_parse
from bento.compat.api \
    import \
        relpath
from bento.core.subpackage \
    import \
        SubPackageDescription, get_extensions, get_compiled_libraries, get_packages
from bento.core.parse_helpers \
    import \
        extract_top_dicts, extract_top_dicts_subento
from bento.core.errors \
    import \
        InvalidPackage, InternalBentoError

def _parse_libraries(libraries):
    ret = {}
    if len(libraries) > 0:
        if not list(libraries.keys()) == ["default"]:
            raise NotImplementedError(
                    "Non default library not yet supported")

        default = libraries["default"]
        for k in ["packages", "py_modules", "install_requires", "sub_directory"]:
            if k in default:
                ret[k] = default[k]

        ret["extensions"] = {}
        for k, v in default.get("extensions", {}).items():
            ret["extensions"][k] = Extension.from_parse_dict(v)

        ret["compiled_libraries"] = {}
        for k, v in default.get("compiled_libraries", {}).items():
            ret["compiled_libraries"][k] = \
                    CompiledLibrary.from_parse_dict(v)
    return ret

def recurse_subentos(subentos, source_dir):
    filenames = []
    subpackages = {}

    # FIXME: this is damn ugly - using nodes would be good here
    def _recurse(subento, cwd):
        f = os.path.normpath(os.path.join(cwd, subento, "bento.info"))
        if not os.path.exists(f):
            raise ValueError("%s not found !" % f)
        filenames.append(relpath(f, source_dir))

        fid = open(f)
        try:
            key = relpath(f, source_dir)
            rdir = relpath(os.path.join(cwd, subento), source_dir)

            d = raw_parse(fid.read(), f)
            kw, subentos = raw_to_subpkg_kw(d)
            subpackages[key] = SubPackageDescription(rdir, **kw)
            hooks_as_abspaths = [os.path.normpath(os.path.join(cwd, subento, h)) \
                                 for h in subpackages[key].hook_files]
            filenames.extend([relpath(f, source_dir) for f in hooks_as_abspaths])
            for s in subentos:
                _recurse(s, os.path.join(cwd, subento))
        finally:
            fid.close()

    for s in subentos:
        _recurse(s, source_dir)
    return subpackages, filenames

def build_libs_from_dict(libraries_d):
    return _parse_libraries(libraries_d)

def build_executables_from_dict(executables_d):
    executables = {}
    for name, executable in executables_d.items():
        executables[name] = Executable.from_parse_dict(executable)
    return executables

def build_data_files_from_dict(data_files_d):
    data_files = {}
    for name, data_file_d in data_files_d.items():
        data_files[name] = DataFiles.from_parse_dict(data_file_d)
    return data_files

def raw_to_subpkg_kw(raw_dict):
    d = build_ast_from_raw_dict(raw_dict)

    libraries_d, misc_d = extract_top_dicts_subento(deepcopy(d))

    kw = {}
    libraries = build_libs_from_dict(libraries_d)
    kw.update(libraries)
    kw["hook_files"] = misc_d["hook_files"]
    sub_directory = kw.pop("sub_directory")
    if sub_directory is not None:
        raise InternalBentoError("Unexpected sub_directory while parsing recursed bendo")

    return kw, misc_d["subento"]

def raw_to_pkg_kw(raw_dict, user_flags, bento_info=None):
    if bento_info is None:
        source_dir = os.getcwd()
    else:
        # bento_info may be a string or a node
        try:
            source_dir = bento_info.parent.abspath()
            bento_info_path = bento_info.srcpath()
        except AttributeError:
            if os.path.isabs(bento_info):
                source_dir = os.path.dirname(bento_info)
                bento_info_path = os.path.basename(bento_info)
            else:
                source_dir = os.getcwd()
                bento_info_path = os.path.basename(bento_info)
                assert bento_info_path == bento_info

    d = build_ast_from_raw_dict(raw_dict, user_flags)

    meta_d, libraries_d, options_d, misc_d = extract_top_dicts(deepcopy(d))
    libraries = build_libs_from_dict(libraries_d)
    executables = build_executables_from_dict(misc_d.pop("executables"))
    data_files = build_data_files_from_dict(misc_d.pop("data_files"))

    kw = {}
    kw.update(meta_d)
    for k in libraries:
        kw[k] = libraries[k]
    kw["executables"] = executables
    kw["data_files"] = data_files

    misc_d.pop("path_options")
    misc_d.pop("flag_options")

    if "subento" in misc_d:
        subentos = misc_d.pop("subento")
        if len(subentos) > 0 and libraries and libraries["sub_directory"] is not None:
            raise InvalidPackage("You cannot use both Recurse and Library:SubDirectory features !")
        else:
            subpackages, files = recurse_subentos(subentos, source_dir=source_dir)
            kw["subpackages"] = subpackages
    else:
        files = []

    kw.update(misc_d)
    if bento_info is not None:
        files.append(bento_info_path)
    files.extend(misc_d["hook_files"])
    # XXX: Do we want to automatically add the hook and bento files in extra
    # source files at the PackageDescription level ?
    kw["extra_source_files"].extend(files)

    if "description_from_file" in kw:
        if bento_info:
            description_file = os.path.join(source_dir, kw["description_from_file"])
        else:
            description_file = kw["description_from_file"]
        if not os.path.exists(description_file):
            raise IOError("Description file %r not found" % (description_file,))
        else:
            f = open(description_file)
            try:
                kw["description"] = f.read()
            finally:
                f.close()
    return kw, files

class PackageDescription:
    @classmethod
    def __from_data(cls, data, user_flags, filename=None):
        if not user_flags:
            user_flags = {}

        d = raw_parse(data, filename)
        kw, files = raw_to_pkg_kw(d, user_flags, filename)
        return cls(**kw)

    @classmethod
    def from_string(cls, s, user_flags=None):
        """Create a PackageDescription from a string containing the package
        description."""
        return cls.__from_data(s, user_flags)

    @classmethod
    def from_file(cls, filename, user_flags=None):
        """Create a PackageDescription from a bento.info file."""
        info_file = open(filename, 'r')
        try:
            data = info_file.read()
            ret = cls.__from_data(data, user_flags, filename)
            return ret
        finally:
            info_file.close()

    # FIXME: this stuff has passed the uglyness threshold quite some time
    # ago...
    def __init__(self, name=None, version=None, summary=None, url=None,
            author=None, author_email=None, maintainer=None,
            maintainer_email=None, license=None, description=None,
            platforms=None, packages=None, py_modules=None, extensions=None,
            install_requires=None, build_requires=None,
            download_url=None, extra_source_files=None, data_files=None,
            classifiers=None, provides=None, obsoletes=None, executables=None,
            hook_files=None, config_py=None, compiled_libraries=None,
            subpackages=None, description_from_file=None, meta_template_file=None,
            keywords=None, sub_directory=None):
        # XXX: should we check that we have sequences when required
        # (py_modules, etc...) ?

        # Package content
        if not packages:
            self.packages = []
        else:
            self.packages = packages

        # Package content
        if not subpackages:
            self.subpackages = {}
        else:
            self.subpackages = subpackages

        if not py_modules:
            self.py_modules = []
        else:
            self.py_modules = py_modules

        if extensions:
            self.extensions = extensions
        else:
            self.extensions = {}
        if compiled_libraries:
            self.compiled_libraries = compiled_libraries
        else:
            self.compiled_libraries = {}

        if not extra_source_files:
            self.extra_source_files = []
        else:
            self.extra_source_files = extra_source_files

        if not data_files:
            self.data_files = {}
        else:
            self.data_files = data_files

        if not executables:
            self.executables = {}
        else:
            self.executables = executables

        pkgs = []
        for p in self.packages:
            pkgs.append(p)
        for p in self.py_modules:
            pkgs.append(p)
        for p in self.extensions.values():
            pkgs.append(p.name)
        top_levels = [i for i in pkgs if not "." in i]

        # Package metadata
        _args = locals()
        kw = dict([(k, _args[k]) for k in _METADATA_FIELDS if k in _args])
        _set_metadata(self, **kw)

        if hook_files is not None:
            self.hook_files = hook_files
        else:
            self.hook_files = []

        if config_py is not None and os.sep != "/":
            self.config_py = unnormalize_path(config_py)
        else:
            self.config_py = config_py

        if meta_template_file is not None and os.sep != "/":
            self.meta_template_file = unnormalize_path(meta_template_file)
        else:
            self.meta_template_file = meta_template_file

        for f in [self.meta_template_file]:
            if f is not None:
                self.extra_source_files.append(f)

        self.sub_directory = sub_directory

def static_representation(pkg, options={}):
    """Return the static representation of the given PackageDescription
    instance as a string."""
    indent_level = 4
    r = []

    def indented_list(head, seq, ind):
        r.append("%s%s:" % (' ' * (ind - 1) * indent_level, head))
        r.append(',\n'.join([' ' * ind * indent_level + i for i in seq]))

    if pkg.name:
        r.append("Name: %s" % pkg.name)
    if pkg.version:
        r.append("Version: %s" % pkg.version)
    if pkg.summary:
        r.append("Summary: %s" % pkg.summary)
    if pkg.url:
        r.append("Url: %s" % pkg.url)
    if pkg.download_url:
        r.append("DownloadUrl: %s" % pkg.download_url)
    if pkg.description:
        lines = pkg.description.splitlines()
        description = [lines[0]]
        if len(lines) > 1:
            description.extend([' ' * indent_level  + line for line in lines[1:]])
        r.append("Description: %s" % "\n".join(description))
    if pkg.author:
        r.append("Author: %s" % pkg.author)
    if pkg.author_email:
        r.append("AuthorEmail: %s" % pkg.author_email)
    if pkg.maintainer:
        r.append("Maintainer: %s" % pkg.maintainer)
    if pkg.maintainer_email:
        r.append("MaintainerEmail: %s" % pkg.maintainer_email)
    if pkg.license:
        r.append("License: %s" % pkg.license)
    if pkg.platforms:
        r.append("Platforms: %s" % ",".join(pkg.platforms))
    if pkg.classifiers:
        indented_list("Classifiers", pkg.classifiers, 1)

    if options:
        for k in options:
            if k == "path_options":
                for p in options["path_options"]:
                    r.append('')
                    r.append("Path: %s" % p.name)
                    r.append(' ' * indent_level + "Description: %s" % p.description)
                    r.append(' ' * indent_level + "Default: %s" % p.default_value)
            else:
                raise ValueError("Gne ? %s" % k)
        r.append('')

    if pkg.extra_source_files:
        indented_list("ExtraSourceFiles", pkg.extra_source_files, 1)
        r.append('')

    if pkg.data_files:
        for section in pkg.data_files.values():
            r.append("DataFiles: %s" % section.name)
            r.append(' ' * indent_level + "SourceDir: %s" % section.source_dir)
            r.append(' ' * indent_level + "TargetDir: %s" % section.target_dir)
            indented_list("Files", section.files, 2)
            r.append('')

    # Fix indentation handling instead of hardcoding it
    if pkg.py_modules or pkg.packages or pkg.extensions:
        r.append("Library:")

        if pkg.install_requires:
            indented_list("InstallRequires", pkg.install_requires, 2)
        if pkg.py_modules:
            indented_list("Modules", pkg.py_modules, 2)
        if pkg.packages:
            indented_list("Packages", pkg.packages, 2)

        if pkg.extensions:
            for name, ext in pkg.extensions.items():
                r.append(' ' * indent_level + "Extension: %s" % name)
                indented_list("Sources", ext.sources, 3)
                if ext.include_dirs:
                    indented_list("IncludeDirs", ext.include_dirs, 3)
        r.append("")

    for name, value in pkg.executables.items():
        r.append("Executable: %s" % name)
        r.append(' ' * indent_level + "Module: %s" % value.module)
        r.append(' ' * indent_level + "Function: %s" % value.function)
        r.append("")
    return "\n".join(r)
