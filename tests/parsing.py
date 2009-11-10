import os
import tempfile
import shutil
import unittest

from os.path import \
    join
from nose.tools import \
    assert_equal

from toydist.cabal_parser.cabal_parser import \
    parse
from toydist.utils import \
    validate_glob_pattern, expand_glob

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

# XXX: known failure
#def test_url_metadata():
#    meta_ref = {
#        "name": "foo",
#        "summary": "A summary",
#        "downloadurl": "http://www.example.com",
#    }
#
#    meta_str = """\
#Name: foo
#Summary: A summary
#DownloadUrl: http://www.example.com
#"""
#
#    parsed = parse(meta_str.splitlines())
#    for k in meta_ref:
#        assert_equal(parsed[k], meta_ref[k])

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

class TestParseGlob(unittest.TestCase):
    def test_invalid(self):
        # Test we raise a ValueError at unwanted pattern
        for p in ["*/a", "src.*", "dir1/dir*/foo"]:
            self.failUnlessRaises(ValueError, lambda: validate_glob_pattern(p))

    def test_simple(self):
        # Test simple pattern matching
        d = tempfile.mkdtemp("flopflop")
        try:
            open(join(d, "foo1.py"), "w").close()
            open(join(d, "foo2.py"), "w").close()
            f = sorted(expand_glob("*.py", d))
            assert_equal(f, ["foo1.py", "foo2.py"])
        finally:
            shutil.rmtree(d)

    def test_simple2(self):
        # Test another pattern matching, with pattern including directory
        d = tempfile.mkdtemp("flopflop")
        try:
            os.makedirs(join(d, "common"))
            open(join(d, "common", "foo1.py"), "w").close()
            open(join(d, "common", "foo2.py"), "w").close()
            f = sorted(expand_glob(join("common", "*.py"), d))
            assert_equal(f, [join("common", "foo1.py"), join("common", "foo2.py")])
        finally:
            shutil.rmtree(d)
