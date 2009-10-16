from distutils.version import \
        StrictVersion

# XXX: this is messy: the grammar is defined as a set of global variables, so
# having more than one AST instance will cause trouble. This cannot be used
# besides prototypes.
from grammar import \
        grammar, name_definition, author_definition, summary_definition, \
        description_definition, modules_definition, extension_definition, \
        package_definition, modules_definition, version_definition

class InvalidFormat(Exception):
    pass

class Extension(object):
    def __init__(self, name, src):
        self.name = name
        self.src = src

    def __repr__(self):
        return "Extension %s (sources are %s)" % (self.name, ",".join(self.src))

def _module_name(t):
    return ".".join(t)

class AST(object):
    # Not really an AST...
    def __init__(self):
        # Metadata
        self.name = None
        self.author = None
        self.description = None
        self.summary = None
        self.version = None

        # Extensions
        self.extensions = []

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
        version_definition.setParseAction(self.parse_version)

        package_definition.setParseAction(self.parse_package)

        modules_definition.setParseAction(self.parse_modules)

        extension_definition.setParseAction(self.parse_extension)

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

    def parse_package(self, s, loc, toks):
        d = toks.asDict()
        for pkg in d['packages']:
            self.packages.append(_module_name(pkg))

    def parse_extension(self, s, loc, toks):
        d = toks.asDict()
        name = _module_name(d['extension_name'])
        src = d['extension_src']
        self.extensions.append(Extension(name, src))

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
Extension: _foo.bar
    sources:
        yo
"""

    ast.parse_string(data)
    print ast.name
    print ast.version
    print ast.summary
    print ast.author
    print ast.description

    print ast.packages

    print ast.py_modules

    print ast.extensions
