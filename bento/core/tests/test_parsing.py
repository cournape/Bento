import os
import tempfile
import shutil
import unittest
import sys

from os.path import \
    join, dirname
from nose.tools import \
    assert_equal, raises

try:
    from cStringIO import StringIO
finally:
    from StringIO import StringIO

from bento.core.pkg_objects import \
    PathOption, FlagOption, Executable, DataFiles
from bento.core.parse_utils import \
    CommaListLexer, comma_list_split
from bento.core.options import \
    PackageOptions

from bento \
    import PackageDescription, static_representation

#old = sys.path[:]
#try:
#    sys.path.insert(0, join(dirname(__file__), "pkgdescr"))
#    from simple_package import PKG, DESCR
#finally:
#    sys.path = old

class TestDataFiles(unittest.TestCase):
    def test_simple(self):
        text = """\
Name: foo

DataFiles: data
    TargetDir: $datadir
    Files:
        foo.data
"""
        r_data = DataFiles("data", files=["foo.data"], target_dir="$datadir")
        pkg = PackageDescription.from_string(text)
        self.failUnless("data" in pkg.data_files)
        assert_equal(pkg.data_files["data"].__dict__, r_data.__dict__)
    
class TestOptions(unittest.TestCase):
    simple_text = """\
Name: foo

Flag: flag1
    Description: flag1 description
    Default: false

Path: foo
    Description: foo description
    Default: /usr/lib
"""
    def _test_simple(self, opts):
        self.failUnless(opts.name, "foo")

        flag = FlagOption("flag1", "false", "flag1 description")
        self.failUnless(opts.flag_options.keys(), ["flags"])
        self.failUnless(opts.flag_options["flag1"], flag.__dict__)

        path = PathOption("foo", "/usr/lib", "foo description")
        self.failUnless(opts.path_options.keys(), ["foo"])
        self.failUnless(opts.path_options["foo"], path.__dict__)

    def test_simple_from_string(self):
        s = self.simple_text
        opts = PackageOptions.from_string(s)
        self._test_simple(opts)

    def test_simple_from_file(self):
        fid, filename = tempfile.mkstemp(suffix=".info", text=True)
        try:
            os.write(fid, self.simple_text.encode())
            opts = PackageOptions.from_file(filename)
            self._test_simple(opts)
        finally:
            os.close(fid)
            os.remove(filename)
