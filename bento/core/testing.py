import os
import sys
import tempfile

from bento.compat.api.moves \
    import \
        unittest
from bento.core.package \
    import \
        raw_parse, raw_to_pkg_kw
from bento.core.pkg_objects \
    import \
        Extension, CompiledLibrary
from bento.core.utils \
    import \
        memoized

if "nose" in sys.modules:
    from bento.core._nose_compat import install_proxy, install_result
    install_proxy()
    install_result()

def skip_if(condition, msg=""):
    return unittest.skipIf(condition, msg)

def expected_failure(f):
    return unittest.expectedFailure(f)

def require_c_compiler(builder="yaku"):
    if builder == "yaku":
        return _require_c_compiler_yaku()
    elif builder == "distutils":
        return _require_c_compiler_distutils()
    else:
        raise ValueError("Unrecognized builder: %r" % builder)

@memoized
def _require_c_compiler_distutils():
    from bento.commands.build_distutils import DistutilsBuilder
    builder = DistutilsBuilder()
    try:
        bld_cmd, compiler = builder._setup_ext()
        if len(compiler.executables) < 1:
            return unittest.skipIf(True, "No C compiler available")
        return unittest.skipIf(False, "")
    except Exception:
        return unittest.skipIf(True, "No C compiler available")

@memoized
def _require_c_compiler_yaku():
    import yaku.context
    source_path = tempfile.mkdtemp()
    build_path = os.path.join(source_path, "build")
    context = yaku.context.get_cfg(src_path=source_path, build_path=build_path)
    try:
        context.use_tools(["pyext", "ctasks"])
        return unittest.skipIf(False, "")
    except ValueError:
        return unittest.skipIf(True, "No C compiler available")

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
        kw["compiled_libraries"] = _kw["compiled_libraries"].values()
    if "extra_source_files" in _kw:
        kw["extra_source_files"] = _kw["extra_source_files"]
    if "sub_directory" in _kw:
        kw["sub_directory"] = _kw["sub_directory"]
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
        extensions = list(_kw["extensions"].values())
    else:
        extensions = []
    if "compiled_libraries" in _kw:
        compiled_libraries = list(_kw["compiled_libraries"].values())
    else:
        compiled_libraries = []
    if "extra_source_files" in _kw:
        extra_source_files = list(_kw["extra_source_files"])
    else:
        extra_source_files = []

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

    return create_fake_package(top_node, packages, py_modules, extensions, compiled_libraries,
                               extra_source_files)

def create_fake_package(top_node, packages=None, modules=None, extensions=None, compiled_libraries=None,
                        extra_source_files=None, sub_directory=None):
    if sub_directory is not None:
        top_or_lib_node = top_node.make_node(sub_directory)
        top_or_lib_node.mkdir()
    else:
        top_or_lib_node = top_node

    if packages is None:
        packages = []
    if modules is None:
        modules = []
    if extensions is None:
        extensions = []
    if compiled_libraries is None:
        compiled_libraries = []
    if extra_source_files is None:
        extra_source_files = []

    for p in packages:
        d = p.replace(".", os.sep)
        n = top_or_lib_node.make_node(d)
        n.mkdir()
        init = n.make_node("__init__.py")
        init.write("")
    for m in modules:
        d = m.replace(".", os.sep)
        n = top_or_lib_node.make_node("%s.py" % d)
        n.parent.mkdir()
        n.write("")
    for extension in extensions:
        main = extension.sources[0]
        n = top_node.make_node(main)
        n.parent.mkdir()
        n.write(DUMMY_C % {"name": extension.name.split(".")[-1]})
        for s in extension.sources[1:]:
            n = top_or_lib_node.make_node(s)
            n.write("")
    for library in compiled_libraries:
        main = library.sources[0]
        n = top_node.make_node(main)
        n.parent.mkdir()
        n.write(DUMMY_CLIB % {"name": library.name.split(".")[-1]})
        for s in library.sources[1:]:
            n = top_or_lib_node.make_node(s)
            n.write("")
    for f in extra_source_files:
        n = top_or_lib_node.find_node(f)
        # FIXME: we don't distinguish between extra_source_files as specified
        # in the bento files and the final extra source file list which contain
        # extra files (including the bento files themselves). We need to create
        # fake files in the former case, but not in the latter.
        if n is None:
            n = top_or_lib_node.make_node(f)
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

