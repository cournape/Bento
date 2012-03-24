import os
import sys
import tempfile
import shutil

import os.path as op

from bento.compat.api.moves \
    import \
        unittest
from bento.core.pkg_objects \
    import \
        DataFiles
from bento.misc.testing \
    import \
        SubprocessTestCase
from bento.core.node \
    import \
        create_first_node
from bento.convert.core \
    import \
        monkey_patch, analyse_setup_py, build_pkg, _convert_numpy_data_files

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

class TestMisc(unittest.TestCase):
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

    def test_convert_numpy_data_files(self):
        source_dir = "foo/bar"
        files = [op.join(source_dir, f) for f in ["foufou", "fubar"]]
        for f in files:
            node = self.top_node.make_node(f)
            node.parent.mkdir()
            node.write("")

        pkg_name, source_dir, target_dir, files = _convert_numpy_data_files(self.top_node, source_dir, files)

        self.assertEqual(pkg_name, "foo.bar")
