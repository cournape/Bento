import os
import shutil
import tempfile

from bento.compat.api.moves \
    import \
        unittest

import bento.core.node as node
import bento.core.pkg_objects as pkg_objects
import bento.core.package as package
import bento.core.subpackage as subpackage

def create_file(file, makedirs=True):
    if makedirs:
        dirname = os.path.dirname(file)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
    fid = open(file, "w").close()

def create_fake_tree(top, files):
    for f in files:
        create_file(os.path.join(top, f))

def clean_tree(files):
    dirs = []
    for f in files:
        dirs.append(os.path.dirname(f))
        if os.path.exists(f):
            os.remove(f)

    for d in sorted(set(dirs))[::-1]:
        os.rmdir(d)

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

        top = tempfile.mkdtemp()
        try:
            create_fake_tree(top, tree)
            root = node.Node("", None)
            top_node = root.find_dir(top)
            extensions = subpackage.flatten_subpackage_extensions(
                    spkg, top_node)
            self.failUnless("foo._hello" in extensions)
            extension = extensions["foo._hello"]
            self.assertEqual(extension.sources, ["foo/src/hellomodule.c"])
            self.assertEqual(extension.include_dirs, ["foo"])
        finally:
            shutil.rmtree(top)

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

        top = tempfile.mkdtemp()
        try:
            create_fake_tree(top, tree)
            root = node.Node("", None)
            top_node = root.find_dir(top)
            clibs = subpackage.flatten_subpackage_compiled_libraries(
                    spkg, top_node)
            self.failUnless("bar.clib" in clibs)
            clib = clibs["bar.clib"]
            self.assertEqual(clib.sources, ["bar/src/clib.c"])
            self.assertEqual(clib.include_dirs, ["bar"])
        finally:
            shutil.rmtree(top)
