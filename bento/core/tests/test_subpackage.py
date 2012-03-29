import shutil
import tempfile

from bento.compat.api.moves \
    import \
        unittest
from bento.core.node \
    import \
        create_first_node, find_root
import bento.core.pkg_objects as pkg_objects
import bento.core.package as package
import bento.core.subpackage as subpackage

def create_fake_tree(top_node, tree):
    for f in tree:
        n = top_node.make_node(f)
        n.parent.mkdir()
        n.write("")

class TestTranslation(unittest.TestCase):
    """Those tests check 'translation' from local definition (as
    defined in the subento file) to the top directory."""
    def test_extension(self):
        tree = [
            "foo/src/hellomodule.c",
            "foo/bento.info",
            "bento.info"]
        extension = pkg_objects.Extension("_hello",
                        sources=["src/hellomodule.c"],
                        include_dirs=["."])
        spkg = package.SubPackageDescription(
                        rdir="foo",
                        extensions={"_hello": extension})

        d = tempfile.mkdtemp()
        try:
            top = create_first_node(d)
            create_fake_tree(top, tree)
            extensions = subpackage.flatten_subpackage_extensions(
                    spkg, top)
            self.failUnless("foo._hello" in extensions)
            extension = extensions["foo._hello"]
            self.assertEqual(extension.sources, ["foo/src/hellomodule.c"])
            self.assertEqual(extension.include_dirs, ["foo"])
        finally:
            shutil.rmtree(d)

    def _test_compiled_library(self, tree, clib, spkg, sources, include_dirs):
        d = tempfile.mkdtemp()
        try:
            top = create_first_node(d)
            create_fake_tree(top, tree)
            clibs = subpackage.flatten_subpackage_compiled_libraries(
                    spkg, top)
            self.failUnless("bar.clib" in clibs)
            clib = clibs["bar.clib"]
            self.assertEqual(clib.sources, sources)
            self.assertEqual(clib.include_dirs, include_dirs)
        finally:
            shutil.rmtree(d)


    def test_compiled_library(self):
        tree = [
            "bar/src/clib.c",
            "bar/bento.info",
            "bento.info"]
        clib = pkg_objects.CompiledLibrary("clib",
                        sources=["src/clib.c"],
                        include_dirs=["."])
        spkg = package.SubPackageDescription(
                        rdir="bar",
                        compiled_libraries={"clib": clib})

        self._test_compiled_library(tree, clib, spkg, ["bar/src/clib.c"], ["bar"])

    def test_compiled_library_glob(self):
        tree = [
            "bar/src/clib.c",
            "bar/src/clib2.c",
            "bar/src/clib3.f",
            "bar/bento.info",
            "bento.info"]
        clib = pkg_objects.CompiledLibrary("clib",
                        sources=["src/*.c", "src/*.f"],
                        include_dirs=["."])
        spkg = package.SubPackageDescription(
                        rdir="bar",
                        compiled_libraries={"clib": clib})

        self._test_compiled_library(tree, clib, spkg, ["bar/src/clib.c", "bar/src/clib2.c", "bar/src/clib3.f"],
                                    ["bar"])
