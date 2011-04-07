import os

from bento._config \
    import \
        BUILD_DIR
from bento.core \
    import \
        PackageDescription, PackageOptions
from bento.commands.configure \
    import \
        ConfigureCommand, _setup_options_parser
from bento.commands.options \
    import \
        OptionsContext
from bento.commands.context \
    import \
        ConfigureYakuContext

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

def prepare_configure(top_node, bento_info, context_klass=ConfigureYakuContext, cmd_argv=None):
    if cmd_argv is None:
        cmd_argv = []

    # FIXME: this should be created in the configure context
    junk_node = top_node.make_node(BUILD_DIR)
    junk_node.mkdir()

    package = PackageDescription.from_string(bento_info)
    package_options = PackageOptions.from_string(bento_info)

    configure = ConfigureCommand()
    opts = OptionsContext()
    for o in ConfigureCommand.common_options:
        opts.add_option(o)

    # FIXME: this emulates the big ugly hack inside bentomaker.
    _setup_options_parser(opts, package_options)

    context = context_klass(configure, cmd_argv, opts, package, top_node)
    context.package_options = package_options

    return context, configure

def create_fake_package_from_bento_info(top_node, bento_info):
    from bento.core.package import raw_parse, raw_to_pkg_kw
    d = raw_parse(bento_info)
    _kw, files = raw_to_pkg_kw(d, {}, None)
    kw = {}
    if "extensions" in _kw:
        kw["extensions"] = _kw["extensions"].values()
    if "py_modules" in _kw:
        kw["modules"] = _kw["py_modules"]
    if "packages" in _kw:
        kw["packages"] = _kw["packages"]
    return create_fake_package(top_node, **kw)

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
        n.parent.mkdir()
        n.write("")
    for extension in extensions:
        main = extension.sources[0]
        n = top_node.make_node(main)
        n.parent.mkdir()
        n.write(DUMMY_C % {"name": extension.name})
        for s in extension.sources[1:]:
            n = top_node.make_node(s)
            n.write("")

