import os
import sys
import mock
import tempfile
import shutil
import errno

import os.path as op

from six.moves \
    import \
        StringIO
from bento.compat.api \
    import \
        NamedTemporaryFile
from bento.compat.api.moves \
    import \
        unittest

from bento.core.utils \
    import \
        subst_vars, to_camel_case, ensure_dir, rename, \
        explode_path, same_content, cmd_is_runnable, memoized, comma_list_split, \
        cpu_count, normalize_path, unnormalize_path, pprint, virtualenv_prefix

def raise_oserror(err):
    ex = OSError()
    ex.errno = err
    raise ex

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

    def test_simple_ensure_dir(self):
        d = tempfile.mkdtemp()
        try:
            new_dir = op.join(d, "foo", "bar")
            new_file = op.join(new_dir, "fubar.txt")
            ensure_dir(new_file)
            self.assertTrue(op.exists(new_dir))
        finally:
            shutil.rmtree(d)

    def _test_rename(self):
        d = tempfile.mkdtemp()
        try:
            f = op.join(d, "f.txt")
            fid = open(f, "wt")
            try:
                fid.write("")
            finally:
                fid.close()
            g = op.join(d, "g.txt")
            rename(f, g)
            self.assertTrue(op.exists(g))
        finally:
            shutil.rmtree(d)

    def test_rename(self):
        self._test_rename()

    @mock.patch("bento.core.utils._rename", lambda x, y: raise_oserror(errno.EXDEV))
    def test_rename_exdev_failure(self):
        self._test_rename()

    @mock.patch("bento.core.utils._rename", lambda x, y: raise_oserror(errno.EBUSY))
    def test_rename_failure(self):
        self.assertRaises(OSError, self._test_rename)

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

    def test_mutable_argument(self):
        lst = []
        @memoized
        def dummy_function(x):
            lst.extend(x)

        dummy_function([1])
        dummy_function([2])
        dummy_function([1])

        self.assertEqual(lst, [1, 2, 1])

    def test_meta(self):
        @memoized
        def dummy_function():
            """some dummy doc"""
        self.assertEqual(repr(dummy_function), "some dummy doc")

    def test_instance_method(self):
        lst = []
        class Foo(object):
            @memoized
            def dummy_function(self, x):
                lst.append(x)
        foo = Foo()
        foo.dummy_function(1)
        foo.dummy_function(1)

        self.assertEqual(lst, [1])

class TestCommaListSplit(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(comma_list_split("-a,-b"), ["-a", "-b"])

class TestPathNormalization(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(normalize_path(r"foo\bar"), "foo/bar")
        self.assertEqual(unnormalize_path("foo/bar"), r"foo\bar")

class TestPPrint(unittest.TestCase):
    def test_simple(self):
        s = StringIO()
        pprint("RED", "foo", s)
        self.assertEqual(s.getvalue(), "\x1b[01;31mfoo\x1b[0m\n")

class TestVirtualEnvPrefix(unittest.TestCase):
    @mock.patch("sys.real_prefix", sys.prefix, create=True)
    def test_no_virtualenv(self):
        self.assertEqual(virtualenv_prefix(), None)

    @mock.patch("sys.real_prefix", sys.prefix, create=True)
    @mock.patch("sys.prefix", "yoyo")
    def test_virtualenv(self):
        self.assertEqual(virtualenv_prefix(), "yoyo")

class TestCpuCount(unittest.TestCase):
    def test_native(self):
        self.assertTrue(cpu_count() > 0)

    @mock.patch("sys.platform", "win32")
    def test_win32(self):
        old = os.environ.get("NUMBER_OF_PROCESSORS", None)
        try:
            os.environ["NUMBER_OF_PROCESSORS"] = "2"
            self.assertEqual(cpu_count(), 2)
        finally:
            if old is not None:
                os.environ["NUMBER_OF_PROCESSORS"] = old

    @mock.patch("sys.platform", "bsd")
    @mock.patch("os.popen", lambda s: StringIO("3"))
    def test_bsd(self):
        self.assertEqual(cpu_count(), 3)
