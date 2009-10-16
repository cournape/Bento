from distutils.version import \
        StrictVersion

from toydist.misc import \
        Extension

# XXX: this is messy: the grammar is defined as a set of global variables, so
# having more than one AST instance will cause trouble. This cannot be used
# besides prototypes.
from grammar import \
        grammar, name_definition, author_definition, summary_definition, \
        description_definition, modules_definition, extension_definition, \
        package_definition, modules_definition, version_definition, \
        author_email_definition, maintainer_definition, \
        maintainer_email_definition, library_definition

class InvalidFormat(Exception):
    pass

def _module_name(t):
    return ".".join(t)

class AST(object):
    # Not really an AST...
    def __init__(self):
        # Metadata
        self.name = None
        self.author = None
        self.author_email = None
        self.maintainer = None
        self.maintainer_email = None
        self.description = None
        self.summary = None
        self.version = None

        self.library = {
                'extensions': [],
                'packages': [],
                'py_modules': []}

        # Packages
        self.packages = []

        # Modules
        self.py_modules = []

        self._set_ast()

    def _set_ast(self):
        name_definition.setParseAction(self.parse_name)

        summary_definition.setParseAction(self.parse_summary)
        description_definition.setParseAction(self.parse_description)

        author_definition.setParseAction(self.parse_author)
        author_email_definition.setParseAction(self.parse_author_email)
        maintainer_definition.setParseAction(self.parse_maintainer)
        maintainer_email_definition.setParseAction(self.parse_maintainer_email)

        version_definition.setParseAction(self.parse_version)

        library_definition.setParseAction(self.parse_library)

        package_definition.setParseAction(self.parse_package)

        modules_definition.setParseAction(self.parse_modules)

        #extension_definition.setParseAction(self.parse_extension)

    def parse_string(self, data):
        return grammar.parseString(data)

    def parse_string(self, data):
        grammar.parseString(data)

    def parse_name(self, s, loc, toks):
        self.name = toks.asDict()['name']

    def parse_summary(self, s, loc, toks):
        self.summary = " ".join(toks.asDict()['summary'])

    def parse_description(self, s, loc, toks):
        self.description = "\n".join(toks.asDict()['description'])

    def parse_author(self, s, loc, toks):
        self.author = " ".join(toks.asDict()['author'])

    def parse_author_email(self, s, loc, toks):
        self.author_email = " ".join(toks.asDict()['author_email'])

    def parse_maintainer(self, s, loc, toks):
        self.maintainer = " ".join(toks.asDict()['maintainer'])

    def parse_maintainer_email(self, s, loc, toks):
        self.maintainer_email = " ".join(toks.asDict()['maintainer_email'])

    def parse_version(self, s, loc, toks):
        version = " ".join(toks.asDict()['version'])
        if not StrictVersion.version_re.match(version):
            raise InvalidFormat("version %s is not a valid version number" \
                                % version)
        self.version = version

    def parse_modules(self, s, loc, toks):
        d = toks.asDict()
        for module in d['modules']:
            self.py_modules.append(_module_name(module))

    def parse_src(self, s, loc, toks):
        pass

    def parse_library(self, s, loc, toks):
        d = toks.asDict()
        if d.has_key('extensions'):
            for ext in d['extensions']:
                ext_d = ext.asDict()
                name = _module_name(ext_d['extension_name'])
                src = [str(s) for s in ext_d['extension_src']]
                self.library['extensions'].append(Extension(name, src))

    def parse_package(self, s, loc, toks):
        d = toks.asDict()
        for pkg in d['packages']:
            self.packages.append(_module_name(pkg))

    def to_dict(self):
        """Return the data as a dict."""
        # XXX: redundancy between this and PackageDescription
        d = {'name': self.name,
            'version': self.version,
            'summary': self.summary,
            'author': self.author,
            'author_email': self.author_email,
            'maintainer': self.maintainer,
            'maintainer_email': self.maintainer_email,
            'description': self.description,
            'packages': self.packages,
            'py_modules': self.py_modules,
            'extensions': self.extensions}

        return d

if __name__ == '__main__':
    ast = AST()

    data = """\
Name: numpy
Version: 1.3.0
Description:
    NumPy is a general-purpose array-processing package designed to
    efficiently manipulate large multi-dimensional arrays of arbitrary
    records without sacrificing too much speed for small multi-dimensional
    arrays.  NumPy is built on the Numeric code base and adds features
    introduced by numarray as well as an extended C-API and the ability to
    create arrays of arbitrary type which also makes NumPy suitable for
    interfacing with general-purpose data-base applications.
    .
    There are also basic facilities for discrete fourier transform,
    basic linear algebra and random number generation.
Summary: array processing for numbers, strings, records, and objects.
Package:
    foo.bar,
    foo.bar2,
    foo.bar3
Modules:
    bar,
    foobar
Author: someone
AuthorEmail: someone@example.com
Maintainer: someonelse
MaintainerEmail: someonelse@example.com
Library:
    Extension: _foo.bar
        sources:
            yo
    Extension: _foo.bar2
        sources:
            yo2
"""

    ast.parse_string(data)
    print ast.name
    print ast.version
    print ast.summary
    print ast.author
    print ast.author_email
    print ast.maintainer
    print ast.maintainer_email
    print ast.description

    print ast.library['extensions']
    print ast.library['py_modules']
    print ast.library['packages']
