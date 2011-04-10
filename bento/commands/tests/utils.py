import os

from bento._config \
    import \
        BUILD_DIR
from bento.core \
    import \
        PackageDescription, PackageOptions
from bento.core.pkg_objects \
    import \
        Extension, CompiledLibrary
from bento.core.package \
    import \
        raw_parse, raw_to_pkg_kw, build_ast_from_raw_dict, PackageDescription
from bento.commands.configure \
    import \
        ConfigureCommand, _setup_options_parser
from bento.commands.build \
    import \
        BuildCommand
from bento.commands.options \
    import \
        OptionsContext
from bento.commands.context \
    import \
        ConfigureYakuContext, BuildYakuContext

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
    opts = OptionsContext.from_command(configure)

    # FIXME: this emulates the big ugly hack inside bentomaker.
    _setup_options_parser(opts, package_options)

    context = context_klass(cmd_argv, opts, package, top_node)
    context.package_options = package_options

    return context, configure

def prepare_build(top_node, pkg, context_klass=BuildYakuContext):
    build = BuildCommand()
    opts = OptionsContext.from_command(build)

    bld = context_klass([], opts, pkg, top_node)
    return bld, build

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

def create_fake_package_from_bento_infos(top_node, bento_infos, bscripts=None):
    if bscripts is None:
        bscripts = {}
    for loc, content in bento_infos.iteritems():
        n = top_node.make_node(loc)
        n.parent.mkdir()
        n.write(content)
    for loc, content in bscripts.iteritems():
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
    packages = _kw.get("packages", [])
    for name, spkg in subpackages.iteritems():
        n = top_node.search(name)
        n.write(bento_infos[name])
        d = n.parent
        for py_module in spkg.py_modules:
            m = d.make_node(py_module)
            py_modules.append(m.path_from(top_node))

        extensions.extend(flatten_extensions(top_node, spkg))
        packages.extend(flatten_packages(top_node, spkg))

    return create_fake_package(top_node, packages, py_modules, extensions)

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
        n.write(DUMMY_C % {"name": extension.name.split(".")[-1]})
        for s in extension.sources[1:]:
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

def flatten_packages(top_node, subpackage):
    ret = {}

    d = top_node.find_dir(subpackage.rdir)
    parent_pkg = ".".join(subpackage.rdir.split("/"))
    return ["%s.%s" % (parent_pkg, p) for p in subpackage.packages]

