import os
import unittest
import tempfile
import shutil

from os.path import \
    join

from bento.core.utils import \
    validate_glob_pattern, expand_glob, subst_vars, to_camel_case, explode_path

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
            self.assertEqual(f, ["foo1.py", "foo2.py"])
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
            self.assertEqual(f, [join("common", "foo1.py"), join("common", "foo2.py")])
        finally:
            shutil.rmtree(d)

class TestSubstVars(unittest.TestCase):
    def test_subst_vars_simple(self):
        d = {'prefix': '/usr/local'}
        self.assertEqual(subst_vars('$prefix', d), d['prefix'])

    def test_subst_vars_recursive(self):
        d = {'prefix': '/usr/local',
             'eprefix': '$prefix',
             'datarootdir': '$prefix/share',
             'datadir': '$datarootdir'}
        self.assertEqual(subst_vars('$eprefix', d), '/usr/local')
        self.assertEqual(subst_vars('$datadir', d), '/usr/local/share')

    def test_subst_vars_escaped(self):
        d = {'prefix': '/usr/local',
             'eprefix': '$prefix',
             'datarootdir': '$prefix/share',
             'datadir': '$datarootdir'}
        self.assertEqual(subst_vars('$datadir', d), '/usr/local/share')
        self.assertEqual(subst_vars('$$datadir', d), '$datadir')

    def test_to_camel_case(self):
        d = [("foo", "Foo"), ("foo_bar", "FooBar"), ("_foo_bar", "_FooBar"), ("__fubar", "__Fubar"),
             ("_fubar_", "_Fubar_")]
        for lower, camel in d:
            self.assertEqual(to_camel_case(lower), camel)

class TestExplodePath(unittest.TestCase):
    def test_simple(self):
        path = "/home/joe"
        self.assertEqual(explode_path(path), ["/", "home", "joe"])

        path = "home/joe"
        self.assertEqual(explode_path(path), ["home", "joe"])

    def test_ends_with_sep(self):
        path = "/home/joe/"
        self.assertEqual(explode_path(path), ["/", "home", "joe"])

    def test_empty(self):
        path = ""
        self.assertEqual(explode_path(path), [])
