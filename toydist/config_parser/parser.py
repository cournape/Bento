from grammar import \
        grammar, name_definition, author_definition, summary_definition, \
        description_definition, modules_definition, extension_definition

def _module_name(t):
    return ".".join(t)

class AST(object):
    # Not really an AST...
    def __init__(self):
        pass

    def parse_name(self, s, loc, toks):
        print "= Name is =\n\t%s" % toks[1]

    def parse_summary(self, s, loc, toks):
        print "= Summary is =\n\t%s" % toks[1]

    def parse_description(self, s, loc, toks):
        print "= Description is =\n\t%s" % "\n\t".join([str(i) for i in toks[0][1]])

    def parse_author(self, s, loc, toks):
        print "= Author is =\n\t%s" % toks[1]

    def parse_modules(self, s, loc, toks):
        def _module_name(t):
            return ".".join(t)
        mods = toks[1:]
        print "= Modules are ="
        for m in mods:
            print module_name(m)

    def parse_extension(self, s, loc, toks):
        def module_name(t):
            return ".".join(t)
        extens = toks[1:]
        print "= Extensions are =", toks
        #for e in extens:
        #    print module_name(e)

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
    grammar.parseString(data)
