from grammar import \
        grammar, name_definition, author_definition, summary_definition, \
        description_definition, modules_definition, extension_definition

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
        self.extensions = []

    def parse_name(self, s, loc, toks):
        pass

    def parse_summary(self, s, loc, toks):
        pass

    def parse_description(self, s, loc, toks):
        pass

    def parse_author(self, s, loc, toks):
        pass

    def parse_modules(self, s, loc, toks):
        pass

    def parse_src(self, s, loc, toks):
        pass

    def parse_extension(self, s, loc, toks):
        d = toks.asDict()
        name = _module_name(d['extension_name'])
        src = d['extension_src']
        self.extensions.append(Extension(name, src))

if __name__ == '__main__':
    ast = AST()

    extension_definition.setParseAction(ast.parse_extension)

    data = """\
Name: numpy
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
Modules:
    foo.bar,
    foo.bar2,
    foo.bar3
Author: someone
Extension: _foo.bar
    sources:
        yo
"""
    tokens = grammar.parseString(data)

    print ast.extensions
