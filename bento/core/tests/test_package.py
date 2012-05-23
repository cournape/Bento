import os
import tempfile

from bento.compat.api.moves \
    import \
        unittest
from bento.core.package \
    import \
        PackageDescription
from bento.core.package import static_representation
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

class TestStaticRepresentation(unittest.TestCase):
    def test_metadata(self):
        bento_info = """\
Name: Sphinx
Version: 0.6.3
Summary: Python documentation generator
Url: http://sphinx.pocoo.org/
DownloadUrl: http://pypi.python.org/pypi/Sphinx
Description: Some long description.
Author: Georg Brandl
AuthorEmail: georg@python.org
Maintainer: Georg Brandl
MaintainerEmail: georg@python.org
License: BSD
Platforms: any
Classifiers:
    Development Status :: 4 - Beta,
    Environment :: Console,
    Environment :: Web Environment,
    Intended Audience :: Developers,
    License :: OSI Approved :: BSD License,
    Operating System :: OS Independent,
    Programming Language :: Python,
    Topic :: Documentation,
    Topic :: Utilities
"""
        self._static_representation(bento_info)

    def test_simple_library(self):
        bento_info = """\
Name: foo

Library:
    Packages: foo
"""
        self._static_representation(bento_info)

    def _static_representation(self, bento_info):
        r_pkg = PackageDescription.from_string(bento_info)
        # We recompute pkg to avoid dealing with stylistic difference between
        # original and static_representation
        pkg = PackageDescription.from_string(static_representation(r_pkg))

        self.assertEqual(static_representation(pkg), static_representation(r_pkg))

class TestPackageMetadata(unittest.TestCase):
    def test_ctor(self):
        meta = PackageMetadata(name="foo", version="1.0", author="John Doe",
                               author_email="john@doe.com")
        self.assertEqual(meta.fullname, "foo-1.0")
        self.assertEqual(meta.contact, "John Doe")
        self.assertEqual(meta.contact_email, "john@doe.com")
