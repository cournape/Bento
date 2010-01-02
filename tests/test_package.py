import unittest
import os
import tempfile

from nose.tools import \
    assert_equal

from toydist import PackageDescription
from toydist.core.package import file_list
from toydist.core.meta import PackageMetadata
from toydist.core.pkg_objects import DataFiles

def create_file(file, makedirs=True):
    if makedirs:
        dirname = os.path.dirname(file)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
    fid = open(file, "w").close()

def clean_tree(files):
    dirs = []
    for f in files:
        dirs.append(os.path.dirname(f))
        if os.path.exists(f):
            os.remove(f)

    for d in sorted(set(dirs))[::-1]:
        os.rmdir(d)

class TestPackage(unittest.TestCase):
    def test_file_list(self):
        # Create a simple package in temp dir, and check file_list(pkg) is what
        # we expect
        _files = [
            "foo/pkg/__init__.py",
            "foo/pkg/yo.py",
            "foo/module.py",
            "foo/data/foo.dat",
        ]

        d = tempfile.mkdtemp()
        files = [os.path.join(d, f) for f in _files]
        try:
            for f in files:
                create_file(f)
            pkg = PackageDescription(name="foo",
                                     packages=["pkg"],
                                     py_modules=["module"],
                                     data_files={"data": 
                                            DataFiles("data", files=["data/foo.dat"],
                                            target="$prefix", srcdir=".")
                                     })
            fl = [os.path.normpath(f) for f in file_list(pkg, root_src=os.path.join(d, "foo"))]
            assert_equal(sorted(fl), sorted(files))
        finally:
            clean_tree(files)
            os.rmdir(d)

class TestPackageMetadata(unittest.TestCase):
    def test_ctor(self):
        meta = PackageMetadata(name="foo", version="1.0", author="John Doe",
                               author_email="john@doe.com")
        assert_equal(meta.fullname, "foo-1.0")
        assert_equal(meta.contact, "John Doe")
        assert_equal(meta.contact_email, "john@doe.com")
