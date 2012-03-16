import os
import shutil
import tempfile

from bento.compat.api.moves \
    import \
        unittest

from bento._config \
    import \
        IPKG_PATH
from bento.core.node \
    import \
        create_root_with_source_tree
from bento.core.package \
    import \
        PackageDescription
from bento.core \
    import \
        PackageMetadata
from bento.core.pkg_objects \
    import \
        Extension
from bento.installed_package_description \
    import \
        InstalledPkgDescription, ipkg_meta_from_pkg
from bento.conv \
    import \
        to_distutils_meta

from bento.commands.egg_utils \
    import \
        EggInfo

DESCR = """\
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

Library:
    Packages:
        sphinx,
        sphinx.builders
    Modules:
        cat.py
    Extension: _dog
        Sources: src/dog.c

Executable: sphinx-build
    Module: sphinx
    Function: main
"""

DUMMY_C = r"""\
#include <Python.h>
#include <stdio.h>

static PyObject*
hello(PyObject *self, PyObject *args)
{
    printf("Hello from C\n");
    Py_INCREF(Py_None);
    return Py_None;
}

static PyMethodDef HelloMethods[] = {
    {"hello",  hello, METH_VARARGS, "Print a hello world."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

PyMODINIT_FUNC
init%(name)s(void)
{
    (void) Py_InitModule("%(name)s", HelloMethods);
}
"""

def create_fake_package(top_node, packages=None, modules=None, extensions=[]):
    if packages is None:
        packages = []
    if modules is None:
        modules = []
    if extensions is None:
        extensions = []

    for p in packages:
        d = p.replace(".", os.sep)
        n = top_node.make_node(d)
        n.mkdir()
        init = n.make_node("__init__.py")
        init.write("")
    for m in modules:
        d = m.replace(".", os.sep)
        n = top_node.make_node("%s.py" % d)
    for extension in extensions:
        main = extension.sources[0]
        n = top_node.make_node(main)
        n.parent.mkdir()
        n.write(DUMMY_C % {"name": extension.name})
        for s in extension.sources[1:]:
            n = top_node.make_node(s)
            n.write("")

class TestEggInfo(unittest.TestCase):
    def setUp(self):
        self.old_dir = None
        self.tmpdir = None

        self.old_dir = os.getcwd()
        self.tmpdir = tempfile.mkdtemp()

        os.chdir(self.tmpdir)
        root = create_root_with_source_tree(self.tmpdir, os.path.join(self.tmpdir, "build"))
        self.run_node = root.find_node(self.tmpdir)
        self.top_node = self.run_node._ctx.srcnode
        self.build_node = self.run_node._ctx.bldnode

    def tearDown(self):
        if self.old_dir:
            os.chdir(self.old_dir)
        if os.path.exists(self.tmpdir):
            shutil.rmtree(self.tmpdir)

    def _prepare_egg_info(self):
        create_fake_package(self.top_node, ["sphinx", "sphinx.builders"],
                            ["cat.py"], [Extension("_dog", [os.path.join("src", "dog.c")])])
        ipkg_file = self.build_node.make_node(IPKG_PATH)
        ipkg_file.parent.mkdir()
        ipkg_file.write("")

        files = [os.path.join("sphinx", "builders", "__init__.py"),
                 os.path.join("sphinx", "__init__.py"),
                 os.path.join("src", "dog.c"),
                 os.path.join("cat.py")]

        pkg = PackageDescription.from_string(DESCR)
        meta = PackageMetadata.from_package(pkg)
        executables = pkg.executables

        return EggInfo(meta, executables, files)

    def test_pkg_info(self):
        egg_info = self._prepare_egg_info()
        res = egg_info.get_pkg_info()
        ref = """\
Metadata-Version: 1.0
Name: Sphinx
Version: 0.6.3
Summary: Python documentation generator
Home-page: http://sphinx.pocoo.org/
Author: Georg Brandl
Author-email: georg@python.org
License: BSD
Download-URL: http://pypi.python.org/pypi/Sphinx
Description: Some long description.
Platform: UNKNOWN
"""
        self.assertEqual(res, ref)

    def test_iter_meta(self):
        egg_info = self._prepare_egg_info()
        for name, content in egg_info.iter_meta(self.build_node):
            pass
