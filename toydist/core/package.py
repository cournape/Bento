import os

from toydist.core.pkg_objects import \
        Extension
from toydist.core.meta import \
        _set_metadata, _METADATA_FIELDS
from toydist.core.utils import \
        find_package, expand_glob
from toydist.core.descr_parser import \
        parse

class PackageDescription:
    @classmethod
    def __from_data(cls, data, user_flags):
        if not user_flags:
            user_flags = {}
        d = parse(data, user_flags)

        kw = {}
        for k in ['name', 'version', 'summary', 'url', 'author',
                'maintainer', 'maintainer_email', 'license',
                'author_email', 'description', 'platforms',
                'install_requires', 'build_requires', 'download_url',
                'classifiers']:
            # FIXME: consolidate this naming mess
            data_key = k.replace('_', '')
            if not d.has_key(data_key):
                kw[k] = None
            else:
                kw[k] = d[data_key]

        if d.has_key('extrasourcefiles'):
            kw['extra_source_files'] = d['extrasourcefiles']
        else:
            kw['extra_source_files'] = []

        if d.has_key('datafiles'):
            kw['data_files'] = d['datafiles']
        else:
            kw['data_files'] = []

        if d.has_key('library'):
            library = d['library'][""]

            if library.has_key('packages'):
                kw['packages'] = library['packages']
            else:
                kw['packages'] = []

            if library.has_key('modules'):
                kw['py_modules'] = library['modules']
            else:
                kw['py_modules'] = []

            if library.has_key('extension'):
                kw['extensions'] = library['extension']
            else:
                kw['extensions'] = []

            if library.has_key('installdepends'):
                kw['install_requires'] = library['installdepends']
            else:
                kw['install_requires'] = []

        if d.has_key('executables'):
            executables = {}
            for name, value in d["executables"].items():
                executables[name] = value
            kw["executables"] = executables
        else:
            kw["executables"] = {}

        return cls(**kw)

    @classmethod
    def from_string(cls, s, user_flags=None):
        """Create a PackageDescription from a string containing the package
        description."""
        return cls.__from_data(s.splitlines(), user_flags)

    @classmethod
    def from_file(cls, filename, user_flags=None):
        """Create a PackageDescription from a toysetup.info file."""
        info_file = open(filename, 'r')
        try:
            data = info_file.readlines()
            return cls.__from_data(data, user_flags)
        finally:
            info_file.close()

    def __init__(self, name, version=None, summary=None, url=None,
            author=None, author_email=None, maintainer=None,
            maintainer_email=None, license=None, description=None,
            platforms=None, packages=None, py_modules=None, extensions=None,
            install_requires=None, build_requires=None,
            download_url=None, extra_source_files=None, data_files=None,
            classifiers=None, provides=None, obsoletes=None, executables=None):
        # XXX: should we check that we have sequences when required
        # (py_modules, etc...) ?

        # Package metadata
        _args = locals()
        kw = dict([(k, _args[k]) for k in _METADATA_FIELDS if k in _args])
        _set_metadata(self, **kw)

        # Package content
        if not packages:
            self.packages = []
        else:
            self.packages = packages

        if not py_modules:
            self.py_modules = []
        else:
            self.py_modules = py_modules

        if not extensions:
            self.extensions = []
        else:
            self.extensions = extensions

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

    @property
    def top_levels(self):
        pkgs = list(set([k.split(".", 1)[0] for k in self.packages]))
        return pkgs

def file_list(pkg, root_src=""):
    # FIXME: root_src
    files = []
    for entry in pkg.extra_source_files:
        files.extend(expand_glob(entry, root_src))

    for p in pkg.packages:
        files.extend(find_package(p, root_src))

    for m in pkg.py_modules:
        files.append(os.path.join(root_src, '%s.py' % m))

    for section in pkg.data_files.values():
        for entry in section.files:
            files.extend([os.path.join(root_src, section.srcdir, f) 
                          for f in expand_glob(entry, root_src)])

    return files

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
        r.append("Description: %s" %
                 "\n".join([' ' * indent_level  + line 
                            for line in pkg.description.splitlines()]))
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
        for section in pkg.data_files:
            v = pkg.data_files[section]
            r.append("DataFiles: %s" % section)
            r.append(' ' * indent_level + "SourceDir: %s" % v["srcdir"])
            r.append(' ' * indent_level + "TargetDir: %s" % v["target"])
            indented_list("Files", v["files"], 2)
            r.append('')

    # Fix indentation handling instead of hardcoding it
    r.append("Library:")

    if pkg.install_requires:
        indented_list("InstallRequires", pkg.install_requires, 2)
    if pkg.py_modules:
        indented_list("Modules", pkg.modules, 2)
    if pkg.packages:
        indented_list("Packages", pkg.packages, 2)

    if pkg.extensions:
        for e in pkg.extensions:
            r.append(' ' * indent_level + "Extension: %s" % e.name)
            indented_list("Sources", e.sources, 3)
    r.append("")

    for name, value in pkg.executables.items():
        r.append("Executable: %s" % name)
        r.append(' ' * indent_level + "Module: %s" % value.module)
        r.append(' ' * indent_level + "Function: %s" % value.function)
        r.append("")
    return "\n".join(r)
