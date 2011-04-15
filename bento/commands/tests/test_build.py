import os
import shutil
import unittest
import tempfile

import nose

from nose.plugins.skip \
    import \
        SkipTest

from bento.core.node \
    import \
        create_root_with_source_tree
from bento.core \
    import \
        PackageDescription
from bento.commands.context \
    import \
        BuildContext, BuildYakuContext, ConfigureYakuContext
from bento.commands.options \
    import \
        OptionsContext, Option
from bento.commands.build \
    import \
        BuildCommand

import bento.commands.build_distutils
import bento.commands.build_yaku

from yaku.context \
    import \
        get_bld, get_cfg

from bento.commands.tests.utils \
    import \
        prepare_configure, create_fake_package, create_fake_package_from_bento_info

BENTO_INFO_WITH_EXT = """\
Name: foo

Library:
    Extension: foo
        Sources: foo.c
"""

BENTO_INFO = """\
Name: foo

Library:
    Packages: foo, foo.bar
    Modules: fubar
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

def skipif(condition, msg=None):
    def skip_decorator(f):
        if callable(condition):
            skip_func = condition
        else:
            skip_func = lambda : condition()

        if skip_func():
            def g(*a, **kw):
                raise SkipTest()
        else:
            g = f
        return nose.tools.make_decorator(f)(g)
    return skip_decorator

def has_numpy():
    try:
        import numpy
        return True
    except ImportError:
        return False

class _TestBuildSimpleExtension(unittest.TestCase):
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

    def _test_simple_extension(self):
        for f, content in [("bento.info", BENTO_INFO_WITH_EXT), ("foo.c", FOO_C)]:
            fid = open(os.path.join(self.d, f), "w")
            try:
                fid.write(content)
            finally:
                fid.close()
        return PackageDescription.from_string(BENTO_INFO_WITH_EXT)

class TestBuildDistutils(_TestBuildSimpleExtension):
    def setUp(self):
        from bento.commands.build_distutils import DistutilsBuilder
        _TestBuildSimpleExtension.setUp(self)
        self._distutils_builder = DistutilsBuilder()

    def test_simple_extension(self):
        pkg = self._test_simple_extension()

        for extension in pkg.extensions.values():
            isection = self._distutils_builder.build_extension(extension)
            self.assertTrue(os.path.exists(os.path.join(isection.source_dir, isection.files[0][0])))


class TestBuildYaku(_TestBuildSimpleExtension):
    def setUp(self):
        super(TestBuildYaku, self).setUp()

        ctx = get_cfg()
        ctx.use_tools(["ctasks", "pyext"])
        ctx.store()

        self.yaku_build = get_bld()

    def _build_extensions(self, pkg):
        return bento.commands.build_yaku.build_extensions(pkg.extensions,
            self.yaku_build, {}, {})

    def tearDown(self):
        try:
            self.yaku_build.store()
        finally:
            super(TestBuildYaku, self).tearDown()

    def test_simple_extension(self):
        pkg = self._test_simple_extension()

        foo = self._build_extensions(pkg)
        isection = foo["foo"]
        self.assertTrue(os.path.exists(os.path.join(isection.source_dir, isection.files[0][0])))

    def test_no_extension(self):
        fid = open(os.path.join(self.d, "bento.info"), "w")
        try:
            fid.write("Name: foo")
        finally:
            fid.close()
        pkg = PackageDescription.from_file("bento.info")
        self._build_extensions(pkg)

class TestBuildCommand(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.root = create_root_with_source_tree(self.d, os.path.join(self.d, "build"))

        self.old_dir = os.getcwd()
        os.chdir(self.d)

    def tearDown(self):
        os.chdir(self.old_dir)
        shutil.rmtree(self.d)

    def test_simple(self):
        root = self.root
        top_node = root.srcnode

        create_fake_package_from_bento_info(top_node, BENTO_INFO)
        conf, configure = prepare_configure(top_node, BENTO_INFO, ConfigureYakuContext)
        configure.run(conf)
        conf.shutdown()

        build = BuildCommand()
        opts = OptionsContext.from_command(build)

        bld = BuildYakuContext([], opts, conf.pkg, top_node)
        build.run(bld)
