import os
import tempfile
import shutil

import os.path as op

from bento.compat.api \
    import \
        NamedTemporaryFile
from bento.compat.api.moves \
    import \
        unittest

from bento.core.utils \
    import \
        validate_glob_pattern, expand_glob, subst_vars, to_camel_case, \
        explode_path, same_content, cmd_is_runnable, memoized

class TestParseGlob(unittest.TestCase):
    def test_invalid(self):
        # Test we raise a ValueError at unwanted pattern
        for p in ["*/a", "src.*", "dir1/dir*/foo"]:
            self.failUnlessRaises(ValueError, lambda: validate_glob_pattern(p))

    def test_simple(self):
        # Test simple pattern matching
        d = tempfile.mkdtemp("flopflop")
        try:
            open(op.join(d, "foo1.py"), "w").close()
            open(op.join(d, "foo2.py"), "w").close()
            f = sorted(expand_glob("*.py", d))
            self.assertEqual(f, ["foo1.py", "foo2.py"])
        finally:
            shutil.rmtree(d)

    def test_simple2(self):
        # Test another pattern matching, with pattern including directory
        d = tempfile.mkdtemp("flopflop")
        try:
            os.makedirs(op.join(d, "common"))
            open(op.join(d, "common", "foo1.py"), "w").close()
            open(op.join(d, "common", "foo2.py"), "w").close()
            f = sorted(expand_glob(op.join("common", "*.py"), d))
            self.assertEqual(f, [op.join("common", "foo1.py"), op.join("common", "foo2.py")])
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

class TestSameFile(unittest.TestCase):
    def test_same(self):
        f1 = NamedTemporaryFile("wt", delete=False)
        try:
            f1.write("fofo")
            f1.close()
            f2 = NamedTemporaryFile("wt", delete=False)
            try:
                f2.write("fofo")
                f2.close()
                self.assertTrue(same_content(f1.name, f2.name))
            finally:
                os.remove(f2.name)
        finally:
            os.remove(f1.name)

    def test_different(self):
        f1 = NamedTemporaryFile("wt", delete=False)
        try:
            f1.write("fofo")
            f1.close()
            f2 = NamedTemporaryFile("wt", delete=False)
            try:
                f2.write("fofa")
                f2.close()
                self.assertFalse(same_content(f1.name, f2.name))
            finally:
                os.remove(f2.name)
        finally:
            os.remove(f1.name)

class TestMisc(unittest.TestCase):
    def test_cmd_is_runnable(self):
        st = cmd_is_runnable(["python", "-c", "''"])
        self.assertTrue(st)

    def test_cmd_is_not_runnable(self):
        st = cmd_is_runnable(["phython", "-c", "''"])
        self.assertFalse(st)

class TestMemoize(unittest.TestCase):
    def test_simple_no_arguments(self):
        lst = []
        @memoized
        def dummy_function():
            lst.append(1)

        dummy_function()
        dummy_function()

        self.assertEqual(lst, [1])

    def test_simple(self):
        lst = []
        @memoized
        def dummy_function(x):
            lst.append(x)

        dummy_function(1)
        dummy_function(2)
        dummy_function(1)

        self.assertEqual(lst, [1, 2])
