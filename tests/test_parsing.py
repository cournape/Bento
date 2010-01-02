import os
import tempfile
import shutil
import unittest
import sys

from os.path import \
    join
from nose.tools import \
    assert_equal

try:
    from cStringIO import StringIO
finally:
    from StringIO import StringIO

from toydist.core.descr_parser import \
    parse
from toydist.core.pkg_objects import \
    PathOption, FlagOption
from toydist.core.parse_utils import \
    CommaListLexer, comma_list_split
from toydist.core.options import \
    PackageOptions

from toydist import PackageDescription, static_representation

old = sys.path[:]
try:
    sys.path.insert(0, "pkgdescr")
    from simple_package import PKG, DESCR
finally:
    sys.path = old

def test_metadata():
    meta_ref = {
        "name": "foo",
        "version": "1.0",
        "summary": "A summary",
        "author": "John Doe",
        "authoremail": "john@doe.com",
        "maintainer": "John DoeDoe",
        "maintaineremail": "john@doedoe.com",
        "license": "BSD",
        "platforms": ["any"]
    }

    meta_str = """\
Name: foo
Version: 1.0
Summary: A summary
Description:     
    Some more complete description of the package, spread over severala
    indented lines
Author: John Doe
AuthorEmail: john@doe.com
Maintainer: John DoeDoe
MaintainerEmail: john@doedoe.com
License: BSD
Platforms: any
"""

    parsed = parse(meta_str.splitlines())
    for k in meta_ref:
        assert_equal(parsed[k], meta_ref[k])

def test_url_metadata():
    meta_ref = {
        "name": "foo",
        "summary": "A summary",
        "downloadurl": "http://www.example.com",
    }

    meta_str = """\
Name: foo
Summary: A summary
DownloadUrl: http://www.example.com
"""

    parsed = parse(meta_str.splitlines())
    for k in meta_ref:
        assert_equal(parsed[k], meta_ref[k])

class TestExtension(unittest.TestCase):
    def setUp(self):
        self.meta_str = """\
Name: hello
Version: 1.0
"""

    def _test(self, main_data, expected):
       data = self.meta_str + main_data
       parsed = parse(data.splitlines())
       assert_equal(parsed["library"][""], expected)

    def test_simple(self):
        data = """\
Library:
    Extension: _bar
        sources:
            hellomodule.c
"""

        expected = {"extension": {"_bar": {"sources": ["hellomodule.c"]}}}
        self._test(data, expected)

    def test_multi_sources(self):
        data = """\
Library:
    Extension: _bar
        sources:
            foobar.c,
            barfoo.c,
"""

        expected = {"extension": {"_bar": {"sources": ["foobar.c", "barfoo.c"]}}}
        self._test(data, expected)

    def test_multi_sources2(self):
        data = """\
Library:
    Extension: _bar
        sources:
            foobar.c, barfoo.c
"""

        expected = {"extension": {"_bar": {"sources": ["foobar.c", "barfoo.c"]}}}
        self._test(data, expected)

class TestCommaListLexer(unittest.TestCase):
    def test_simple(self):
        s = ["foo, bar"]
        s += ["""\
foo,
bar"""]

        for i in s:
            lexer = CommaListLexer(i)
            r = [lexer.get_token().strip() for j in range(2)]
            assert_equal(r, ['foo', 'bar'])
            assert lexer.get_token() == lexer.eof

    def test_escape(self):
        s = "foo\,bar"
        lexer = CommaListLexer(s)
        r = lexer.get_token().strip()
        assert_equal(r, 'foo,bar')
        assert lexer.get_token() == lexer.eof

        s = "src\,/_foo.c, bar.c"
        lexer = CommaListLexer(s)
        r = [lexer.get_token().strip() for j in range(2)]
        assert_equal(r, ['src,/_foo.c', 'bar.c'])
        assert lexer.get_token() == lexer.eof

def test_comma_list_split():
    for test in [('foo', ['foo']), ('foo,bar', ['foo', 'bar']),
            ('foo\,bar', ['foo,bar']),
            ('foo.c\,bar.c', ['foo.c,bar.c'])]:
        assert_equal(comma_list_split(test[0]), test[1])

class TestPackage(unittest.TestCase):
    __meta_simple = {
            "name": "Sphinx",
            "version": "0.6.3",
            "summary": "Python documentation generator",
            "url": "http://sphinx.pocoo.org/",
            "download_url": "http://pypi.python.org/pypi/Sphinx",
            "description": "Some long description.",
            "author": "Georg Brandl",
            "author_email": "georg@python.org",
            "maintainer": "Georg Brandl",
            "maintainer_email": "georg@python.org",
            "license": "BSD",
            "platforms": ["any"],
            "classifiers": [
                "Development Status :: 4 - Beta",
                "Environment :: Console",
                "Environment :: Web Environment",
                "Intended Audience :: Developers",
                "License :: OSI Approved :: BSD License",
                "Operating System :: OS Independent",
                "Programming Language :: Python",
                "Topic :: Documentation",
                "Topic :: Utilities",]
        }

    def _test_roundtrip(self, data):
        r_pkg = PackageDescription(**data)
        static = static_representation(r_pkg)
        fid, filename = tempfile.mkstemp("yo")
        try:
            os.write(fid, static)
            pkg = PackageDescription.from_file(filename)
        finally:
            os.close(fid)
            os.remove(filename)
            
        for k in pkg.__dict__:
            assert_equal(pkg.__dict__[k], r_pkg.__dict__[k])

    def test_roundrip_meta(self):
        data = self.__meta_simple
        data["description"] = """\
Sphinx is a tool that makes it easy to create intelligent and beautiful
documentation for Python projects (or other documents consisting of
multiple reStructuredText sources), written by Georg Brandl.
It was originally created to translate the new Python documentation,
but has now been cleaned up in the hope that it will be useful to many
other projects.

Sphinx uses reStructuredText as its markup language, and many of its strengths
come from the power and straightforwardness of reStructuredText and its
parsing and translating suite, the Docutils.

Although it is still under constant development, the following features
are already present, work fine and can be seen "in action" in the Python docs:

* Output formats: HTML (including Windows HTML Help), plain text and LaTeX,
  for printable PDF versions
* Extensive cross-references: semantic markup and automatic links
  for functions, classes, glossary terms and similar pieces of information
* Hierarchical structure: easy definition of a document tree, with automatic
  links to siblings, parents and children
* Automatic indices: general index as well as a module index
* Code handling: automatic highlighting using the Pygments highlighter
* Various extensions are available, e.g. for automatic testing of snippets
  and inclusion of appropriately formatted docstrings.

A development egg can be found `here
<http://bitbucket.org/birkenfeld/sphinx/get/tip.gz#egg=Sphinx-dev>`_."""
        self._test_roundtrip(data)

    #def test_simple_package(self):
    #    pkg = PackageDescription.from_string(DESCR)
    #    for k in PKG.__dict__:
    #        assert_equal(PKG.__dict__[k], pkg.__dict__[k])

class TestFlags(unittest.TestCase):
    def test_simple(self):
        text = """\
Name: foo

Flag: flag1
    description: flag1 description
    default: false
"""
        m = parse(text.splitlines())
        self.failUnless(m["flags"], "false")

    def test_user_custom(self):
        text = """\
Name: foo

Flag: flag1
    description: flag1 description
    default: false
"""
        m = parse(text.splitlines(), user_flags={"flag1": False})
        self.failUnless(m["flags"], "false")

        m = parse(text.splitlines(), user_flags={"flag1": True})
        self.failUnless(m["flags"], "true")

class TestOptions(unittest.TestCase):
    def test_simple(self):
        text = """\
Name: foo

Flag: flag1
    description: flag1 description
    default: false

Path: foo
    description: foo description
    default: /usr/lib
"""
        s = StringIO(text)
        try:
            opts = PackageOptions.from_string(s)
            self.failUnless(opts.name, "foo")
            self.failUnless(opts.flag_options.keys(), ["flags"])
            self.failUnless(opts.flag_options["flag1"].name, "flag1")
            self.failUnless(opts.flag_options["flag1"].default_value, "false")
            self.failUnless(opts.flag_options["flag1"].description, "flag1 description")

            self.failUnless(opts.path_options.keys(), ["foo"])
            self.failUnless(opts.path_options["foo"].name, "foo")
            self.failUnless(opts.path_options["foo"].default_value, "/usr/lib")
            self.failUnless(opts.path_options["foo"].description, "foo description")
        finally:
            s.close()
