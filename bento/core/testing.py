import os

import nose

from nose.plugins.errorclass \
    import \
        ErrorClass, ErrorClassPlugin
from nose.plugins.skip \
    import \
        SkipTest

from bento.core.package \
    import \
        raw_parse, raw_to_pkg_kw
from bento.core.pkg_objects \
    import \
        Extension, CompiledLibrary

class KnownFailureTest(Exception):
    pass

class KnownFailure(ErrorClassPlugin):
    '''Plugin that installs a KNOWNFAIL error class for the
    KnownFailureClass exception.  When KnownFailureTest is raised,
    the exception will be logged in the knownfail attribute of the
    result, 'K' or 'KNOWNFAIL' (verbose) will be output, and the
    exception will not be counted as an error or failure.'''
    enabled = True
    knownfail = ErrorClass(KnownFailureTest,
                           label='KNOWNFAIL',
                           isfailure=False)

    def options(self, parser, env=os.environ):
        env_opt = 'NOSE_WITHOUT_KNOWNFAIL'
        parser.add_option('--no-knownfail', action='store_true',
                          dest='noKnownFail', default=env.get(env_opt, False),
                          help='Disable special handling of KnownFailureTest '
                               'exceptions')

    def configure(self, options, conf):
        if not self.can_configure:
            return
        self.conf = conf
        disable = getattr(options, 'noKnownFail', False)
        if disable:
            self.enabled = False


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

# Code taken from Numpy
def knownfailureif(fail_condition, msg=None):
    """
    Make function raise KnownFailureTest exception if given condition is true.

    If the condition is a callable, it is used at runtime to dynamically
    make the decision. This is useful for tests that may require costly
    imports, to delay the cost until the test suite is actually executed.

    Parameters
    ----------
    fail_condition : bool or callable
        Flag to determine whether to mark the decorated test as a known
        failure (if True) or not (if False).
    msg : str, optional
        Message to give on raising a KnownFailureTest exception.
        Default is None.

    Returns
    -------
    decorator : function
        Decorator, which, when applied to a function, causes SkipTest
        to be raised when `skip_condition` is True, and the function
        to be called normally otherwise.

    Notes
    -----
    The decorator itself is decorated with the ``nose.tools.make_decorator``
    function in order to transmit function name, and various other metadata.

    """
    if msg is None:
        msg = 'Test skipped due to known failure'

    # Allow for both boolean or callable known failure conditions.
    if callable(fail_condition):
        fail_val = lambda : fail_condition()
    else:
        fail_val = lambda : fail_condition

    def knownfail_decorator(f):
        # Local import to avoid a hard nose dependency and only incur the
        # import time overhead at actual test-time.
        def knownfailer(*args, **kwargs):
            if fail_val():
                raise KnownFailureTest(msg)
            else:
                return f(*args, **kwargs)
        return nose.tools.make_decorator(f)(knownfailer)

    return knownfail_decorator

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

DUMMY_CLIB = r"""\
int hello(void)
{
    return 0;
}
"""
def create_fake_package_from_bento_info(top_node, bento_info):
    d = raw_parse(bento_info)
    _kw, files = raw_to_pkg_kw(d, {}, None)
    kw = {}
    if "extensions" in _kw:
        kw["extensions"] = _kw["extensions"].values()
    if "py_modules" in _kw:
        kw["modules"] = _kw["py_modules"]
    if "packages" in _kw:
        kw["packages"] = _kw["packages"]
    if "compiled_libraries" in _kw:
        kw["compiled_libraries"] = _kw["compiled_libraries"]
    return create_fake_package(top_node, **kw)

def create_fake_package_from_bento_infos(top_node, bento_infos, bscripts=None):
    if bscripts is None:
        bscripts = {}
    for loc, content in bento_infos.items():
        n = top_node.make_node(loc)
        n.parent.mkdir()
        n.write(content)
    for loc, content in bscripts.items():
        n = top_node.make_node(loc)
        n.parent.mkdir()
        n.write(content)

    d = raw_parse(bento_infos["bento.info"])
    _kw, files = raw_to_pkg_kw(d, {}, None)
    subpackages = _kw.get("subpackages", {})

    py_modules = _kw.get("py_modules", [])
    if "extensions" in _kw:
        extensions = _kw["extensions"].values()
    else:
        extensions = []
    if "compiled_libraries" in _kw:
        compiled_libraries = _kw["compiled_libraries"].values()
    else:
        compiled_libraries = []
    packages = _kw.get("packages", [])
    for name, spkg in subpackages.items():
        n = top_node.search(name)
        n.write(bento_infos[name])
        d = n.parent
        for py_module in spkg.py_modules:
            m = d.make_node(py_module)
            py_modules.append(m.path_from(top_node))

        extensions.extend(flatten_extensions(top_node, spkg))
        compiled_libraries.extend(flatten_compiled_libraries(top_node, spkg))
        packages.extend(flatten_packages(top_node, spkg))

    return create_fake_package(top_node, packages, py_modules, extensions, compiled_libraries)

def create_fake_package(top_node, packages=None, modules=None, extensions=None, compiled_libraries=None):
    if packages is None:
        packages = []
    if modules is None:
        modules = []
    if extensions is None:
        extensions = []
    if compiled_libraries is None:
        compiled_libraries = []

    for p in packages:
        d = p.replace(".", os.sep)
        n = top_node.make_node(d)
        n.mkdir()
        init = n.make_node("__init__.py")
        init.write("")
    for m in modules:
        d = m.replace(".", os.sep)
        n = top_node.make_node("%s.py" % d)
        n.parent.mkdir()
        n.write("")
    for extension in extensions:
        main = extension.sources[0]
        n = top_node.make_node(main)
        n.parent.mkdir()
        n.write(DUMMY_C % {"name": extension.name.split(".")[-1]})
        for s in extension.sources[1:]:
            n = top_node.make_node(s)
            n.write("")
    for library in compiled_libraries:
        main = library.sources[0]
        n = top_node.make_node(main)
        n.parent.mkdir()
        n.write(DUMMY_CLIB % {"name": library.name.split(".")[-1]})
        for s in library.sources[1:]:
            n = top_node.make_node(s)
            n.write("")

# FIXME: Those flatten extensions are almost redundant with the ones in
# bento.core.subpackages. Here, we do not ensure that the nodes actually exist
# on the fs (make_node vs find_node). But maybe we do not need to check file
# existence in bento.core.subpackages either (do it at another layer)
def flatten_extensions(top_node, subpackage):
    ret = []

    d = top_node.find_dir(subpackage.rdir)
    root_name = ".".join(subpackage.rdir.split("/"))
    for extension in subpackage.extensions.values():
        sources = [d.make_node(s).path_from(top_node) for s in extension.sources]
        full_name = root_name + ".%s" % extension.name
        ret.append(Extension(full_name, sources))
    return ret

def flatten_compiled_libraries(top_node, subpackage):
    ret = []

    d = top_node.find_dir(subpackage.rdir)
    root_name = ".".join(subpackage.rdir.split("/"))
    for library in subpackage.compiled_libraries.values():
        sources = [d.make_node(s).path_from(top_node) for s in library.sources]
        full_name = root_name + ".%s" % library.name
        ret.append(CompiledLibrary(full_name, sources))
    return ret

def flatten_packages(top_node, subpackage):
    ret = {}

    d = top_node.find_dir(subpackage.rdir)
    parent_pkg = ".".join(subpackage.rdir.split("/"))
    return ["%s.%s" % (parent_pkg, p) for p in subpackage.packages]

