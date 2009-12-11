import os

from toydist.misc import \
        Extension

from toydist.utils import \
        find_package
from toydist.cabal_parser.cabal_parser import \
        parse

class PackageDescription:
    @classmethod
    def from_file(cls, filename):
        """Create a PackageDescription from a toysetup.info file."""
        info_file = open(filename, 'r')
        try:
            data = info_file.readlines()
            d = parse(data)

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

            return cls(**kw)
        finally:
            info_file.close()

    def __init__(self, name, version=None, summary=None, url=None,
            author=None, author_email=None, maintainer=None,
            maintainer_email=None, license=None, description=None,
            platforms=None, packages=None, py_modules=None, extensions=None,
            install_requires=None, build_requires=None,
            download_url=None, extra_source_files=None, data_files=None,
            classifiers=None):
        # XXX: should we check that we have sequences when required
        # (py_modules, etc...) ?

        # Package metadata
        self.name = name

        if not version:
            # Distutils default
            self.version = '0.0.0'
        else:
            self.version = version

        self.summary = summary
        self.url = url
        self.download_url = download_url
        self.author = author
        self.author_email = author_email
        self.maintainer = maintainer
        self.maintainer_email = maintainer_email
        self.license = license
        self.description = description

        if not install_requires:
            self.install_requires = []
        else:
            self.install_requires = install_requires

        if not build_requires:
            self.build_requires = []
        else:
            self.build_requires = build_requires

        if not platforms:
            self.platforms = []
        else:
            self.platforms = platforms

        if not classifiers:
            self.classifiers = []
        else:
            self.classifiers = classifiers

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
            self.data_files = []
        else:
            self.data_files = data_files

    def to_dict(self):
        """Return a distutils.core.setup compatible dict."""
        d = {'name': self.name,
            'version': self.version,
            'description': self.summary,
            'url': self.url,
            'author': self.author,
            'author_email': self.author_email,
            'maintainer': self.maintainer,
            'maintainer_email': self.maintainer_email,
            'license': self.license,
            'long_description': self.description,
            'platforms': self.platforms,
            'py_modules': self.py_modules,
            'ext_modules': self.extensions,
            'packages': self.packages,
            'install_requires': self.install_requires}

        return d

def file_list(pkg, root_src=""):
    # FIXME: root_src
    files = []
    files.extend(pkg.extra_source_files)

    for p in pkg.packages:
        files.extend(find_package(p, root_src))

    for m in pkg.py_modules:
        files.append(os.path.join(root_src, '%s.py' % m))

    for section in pkg.data_files.values():
        srcdir_field = section['srcdir']
        files_field = section['files']
        files.extend([os.path.join(srcdir_field, f) for f in files_field])

    return files

def _parse_library(parsed_dict, package_dict):
    package_dict['extensions'] = []
    package_dict['py_modules'] = []
    package_dict['packages'] = []

    for libname, lib in parsed_dict.items():
        if lib.has_key('extension'):
            for ext_name, ext_package_dict in lib['extension'].items():
                src =  ext_package_dict['sources']
                ext = Extension(ext_name, src)
                package_dict['extensions'].append(ext)
        if lib.has_key('modules'):
            package_dict['py_modules'].extend(lib['modules'])
        if lib.has_key('packages'):
            package_dict['packages'].extend(lib['packages'])

def _parse_static(cnt):
    """Parse a static file. cnt is assumed to be the content of the static file
    in a list of strings"""
    data = {}
    res = parse(cnt)

    # Get metadata
    for k in ['name', 'author', 'version', 'url', 'license', 'maintainer',
              'summary', 'description']:
        try:
            val = res[k]
            data[k] = val
            del res[k]
        except KeyError:
            pass

    # Get library section
    if res.has_key('library'):
        _parse_library(res['library'], data)
    return PackageDescription(**data)

def parse_static(filename):
    f = open(filename)
    try:
        return _parse_static(f.readlines())
    finally:
        f.close()

def static_representation(pkg, options={}):
    """Return the static representation of the given PackageDescription
    instance as a string."""
    indent_level = 4
    r = []
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
        r.append("Classifiers:")
        r.extend([' ' * (indent_level * 1) + f + ',' for f in pkg.classifiers])

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
        r.append("ExtraSourceFiles:")
        r.extend([' ' * (indent_level * 1) + f + ',' for f in pkg.extra_source_files])
        r.append('')

    if pkg.data_files:
        for section in pkg.data_files:
            v = pkg.data_files[section]
            r.append("DataFiles: %s" % section)
            r.append(' ' * indent_level + "srcdir:%s" % v["srcdir"])
            r.append(' ' * indent_level + "target:%s" % v["target"])
            r.append(' ' * indent_level + "files:")
            r.extend([' ' * (indent_level * 2) + f + ',' for f in v["files"]])
            r.append('')

    # Fix indentation handling instead of hardcoding it
    r.append("Library:")

    if pkg.install_requires:
        r.append(' ' * indent_level + "InstallDepends:")
        r.extend([' ' * (indent_level * 2) + p + ',' for p in pkg.install_requires])
    if pkg.py_modules:
        r.append(' ' * indent_level + "Modules:")
        r.extend([' ' * (indent_level * 2) + p + ',' for p in pkg.py_modules])
    if pkg.packages:
        r.append(' ' * indent_level + "Packages:")
        r.extend([' ' * (indent_level * 2) + p + ',' for p in pkg.packages])

    if pkg.extensions:
        for e in pkg.extensions:
            r.append(' ' * indent_level + "Extension: %s" % e.name)
            r.append(' ' * 2 * indent_level + "sources:")
            r.extend([' ' * (indent_level * 3) + s + ',' for s in e.sources])
    r.append("")

    return "\n".join(r)
