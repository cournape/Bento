from toydist.misc import \
        Extension

from toydist.config_parser.parser import \
        AST

class PackageDescription:
    def __init__(self, name, version=None, summary=None, url=None,
            author=None, author_email=None, maintainer=None,
            maintainer_email=None, license=None, description=None,
            platforms=None, packages=None, py_modules=None, extensions=None):
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
            'packages': self.packages}

        return d


def _parse_static(cnt):
    """Parse a static file. cnt is assumed to be the content of the static file
    in one string"""
    ast = AST()
    ast.parse_string(cnt)
    return PackageDescription(**ast.to_dict())

def parse_static(filename):
    f = open(filename)
    try:
        cnt = "\n".join(f.readlines())
        return _parse_static(cnt)
    finally:
        f.close()

def static_representation(pkg):
    """Return the static representation of the given PackageDescription
    instance as a string."""
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
        r.append("Description: %s" % pkg.description)
    if pkg.author:
        r.append("Author: %s" % pkg.author)
    if pkg.author_email:
        r.append("AuthorEmail: %s" % pkg.author_email)
    if pkg.maintainer:
        r.append("Author: %s" % pkg.maintainer)
    if pkg.maintainer_email:
        r.append("AuthorEmail: %s" % pkg.maintainer_email)
    if pkg.py_modules:
        r.append("""\
Modules:
    %s""" % "    \n,".join(pkg.py_modules))
    if pkg.packages:
        r.append("""\
Package:
    %s""" % "    \n,".join(pkg.packages))

    if pkg.extensions:
        for e in pkg.extensions:
            r.append("""\
Extension: %s
    sources:
        %s""" % (e.name, "        \n,".join(e.sources)))


    return "\n".join(r)

