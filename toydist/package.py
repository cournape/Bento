from toydist.misc import \
        Extension

from toydist.cabal_parser.cabal_parser import \
        parse

class PackageDescription:
    def __init__(self, name, version=None, summary=None, url=None,
            author=None, author_email=None, maintainer=None,
            maintainer_email=None, license=None, description=None,
            platforms=None, packages=None, py_modules=None, extensions=None,
            install_requires=None, build_requires=None):
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
        self.author = author
        self.author_email = author_email
        self.maintainer = maintainer
        self.maintainer_email = maintainer_email
        self.license = license
        self.description = description

        if not install_requires:
            self.requires = []
        else:
            self.requires = install_requires

        if not build_requires:
            self.build_requires = []
        else:
            self.build_requires = build_requires

        if not platforms:
            self.platforms = []
        else:
            self.platforms = platforms

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
            'install_requires': self.requires}

        return d

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

def static_representation(pkg):
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

    # Fix indentation handling instead of hardcoding it
    r.append("Library:")

    if pkg.py_modules:
        r.append(' ' * indent_level + "Modules:")
        r.extend([' ' * (indent_level * 2) + p + ',' for p in pkg.py_modules])
    if pkg.packages:
        r.append(' ' * indent_level + "Packages:")
        r.extend([' ' * (indent_level * 2) + p + ',' for p in pkg.packages])

    if pkg.extensions:
        for e in pkg.extensions:
            r.append("""\
    Extension: %s
        sources:
            %s""" % (e.name, "            \n,".join(e.sources)))


    return "\n".join(r)

