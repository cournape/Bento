import os
import sys
import tempfile
import shutil

import os.path as op

from bento.compat.api.moves \
    import \
        unittest
from bento.core.package \
    import \
        PackageDescription
from bento.core.pkg_objects \
    import \
        DataFiles
from bento.testing.sub_test_case \
    import \
        SubprocessTestCase
from bento.core.node \
    import \
        create_first_node
from bento.convert.core \
    import \
        monkey_patch, analyse_setup_py, build_pkg, _convert_numpy_data_files, prune_extra_files

class CommonTest(SubprocessTestCase):
    def setUp(self):
        self.save = os.getcwd()
        self.d = tempfile.mkdtemp()
        os.chdir(self.d)
        try:
            self.top_node = create_first_node(self.d)
        except Exception:
            os.chdir(self.save)
            raise

    def tearDown(self):
        os.chdir(self.save)
        shutil.rmtree(self.d)

class TestMonkeyPatch(CommonTest):
    def test_distutils(self):
        monkey_patch(self.top_node, "distutils", "setup.py")
        self.assertTrue("setuptools" not in sys.modules)

    def test_setuptools(self):
        monkey_patch(self.top_node, "setuptools", "setup.py")
        self.assertTrue("setuptools" in sys.modules)

class TestBuildPackage(CommonTest):
    def test_setuptools_include_package(self):
        top = self.top_node

        top.make_node("yeah.txt").write("")
        top.make_node("foo").mkdir()
        top.find_node("foo").make_node("__init__.py").write("")
        top.find_node("foo").make_node("foo.info").write("")
        top.make_node("MANIFEST.in").write("""\
include yeah.txt
include foo/foo.info
""")

        top.make_node("setup.py").write("""\
import setuptools
from distutils.core import setup

setup(name="foo", include_package_data=True, packages=["foo"])
""")

        monkey_patch(top, "setuptools", "setup.py")
        dist, package_objects = analyse_setup_py("setup.py", ["-n", "-q"])
        pkg, options = build_pkg(dist, package_objects, top)

        self.assertEqual(pkg.data_files, {"foo_data": DataFiles("foo_data", ["foo.info"], "$sitedir/foo", "foo")})
        self.assertEqual(pkg.extra_source_files, ["setup.py", "yeah.txt"])

    def test_scripts(self):
        top = self.top_node

        top.make_node("foo").write("")

        top.make_node("setup.py").write("""\
from distutils.core import setup

setup(name="foo", scripts=["foo"])
""")

        monkey_patch(top, "distutils", "setup.py")
        dist, package_objects = analyse_setup_py("setup.py", ["-n", "-q"])
        pkg, options = build_pkg(dist, package_objects, top)

        self.assertEqual(pkg.data_files, {"foo_scripts": DataFiles("foo_scripts", ["foo"], "$bindir", ".")})

class TestMisc(unittest.TestCase):
    def setUp(self):
        super(TestMisc, self).setUp()
        self.save = os.getcwd()
        self.d = tempfile.mkdtemp()
        os.chdir(self.d)
        try:
            self.top_node = create_first_node(self.d)
        except Exception:
            os.chdir(self.save)
            raise

    def tearDown(self):
        os.chdir(self.save)
        shutil.rmtree(self.d)

        super(TestMisc, self).tearDown()

    def test_convert_numpy_data_files(self):
        source_dir = "foo/bar"
        files = [op.join(source_dir, f) for f in ["foufou", "fubar"]]
        for f in files:
            node = self.top_node.make_node(f)
            node.parent.mkdir()
            node.write("")

        pkg_name, source_dir, target_dir, files = _convert_numpy_data_files(self.top_node, source_dir, files)

        self.assertEqual(pkg_name, "foo.bar")

    def test_prune_extra_files(self):
        files = ["doc/foo.info", "yeah.txt", "foo/__init__.py"]
        for f in files:
            n = self.top_node.make_node(f)
            n.parent.mkdir()
            n.write("")

        bento_info = """\
Name: foo

ExtraSourceFiles: yeah.txt

DataFiles: doc
    SourceDir: .
    TargetDir: $sitedir
    Files: doc/foo.info

Library:
    Packages: foo
"""
        pkg = PackageDescription.from_string(bento_info)
        files = prune_extra_files(files, pkg, self.top_node)
        self.assertEqual(files, ["yeah.txt"])
