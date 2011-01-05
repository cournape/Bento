import unittest
import os
import tempfile

from nose.tools import \
    assert_equal

from bento import PackageDescription
from bento.core.package import file_list
from bento.core.meta import PackageMetadata
from bento.core.pkg_objects import DataFiles
from bento.core.node import Node

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
            os.path.join("pkg", "__init__.py"),
            os.path.join("pkg", "yo.py"),
            os.path.join("module.py"),
            os.path.join("data", "foo.dat"),
        ]

        d = tempfile.mkdtemp()
        root = Node("", None)
        top_node = root.find_dir(d)
        files = [os.path.join(d, "foo", f) for f in _files]
        try:
            for f in files:
                create_file(f)
            pkg = PackageDescription(name="foo",
                                     packages=["pkg"],
                                     py_modules=["module"],
                                     data_files={"data": 
                                            DataFiles("data", files=["data/foo.dat"],
                                            target_dir="$prefix",
                                            source_dir=".")
                                     })
            fl = [os.path.normpath(f) for f in file_list(pkg, top_node.find_dir("foo"))]
            assert_equal(sorted(fl), sorted(_files))
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
