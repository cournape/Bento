import os
import shutil
import unittest
import tempfile

from bento.core \
    import \
        PackageDescription
from bento.commands.build_distutils \
    import \
        build_extensions

BENTO_INFO = """\
Name: foo

Library:
    Extension: foo
        Sources: foo.c
"""

FOO_C = r"""\
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
init_bar(void)
{
    (void) Py_InitModule("_bar", HelloMethods);
}
"""

class TestBuild(unittest.TestCase):
    def setUp(self):
        self.save = None
        self.d = None

        self.save = os.getcwd()
        self.d = tempfile.mkdtemp()
        os.chdir(self.d)

    def tearDown(self):
        if self.save:
            os.chdir(self.save)
        if self.d:
            shutil.rmtree(self.d)

    def test_simple_extension(self):
        for f, content in [("bento.info", BENTO_INFO), ("foo.c", FOO_C)]:
            fid = open(os.path.join(self.d, f), "w")
            try:
                fid.write(content)
            finally:
                fid.close()
        pkg = PackageDescription.from_string(BENTO_INFO)
        foo = build_extensions(pkg)
        isection = foo["foo"]
        self.assertTrue(os.path.exists(os.path.join(isection.source_dir, isection.files[0][0])))

    def test_no_extension(self):
        fid = open(os.path.join(self.d, "bento.info"), "w")
        try:
            fid.write("Name: foo")
        finally:
            fid.close()
        pkg = PackageDescription.from_file("bento.info")
        foo = build_extensions(pkg)
