import distutils
import sys

from cPickle \
    import \
        dump

from yaku.pyext \
    import \
        create_pyext, get_pyenv

from yaku.task_manager \
    import \
        get_bld, CACHE_FILE, create_tasks, run_tasks
from yaku.tools \
    import \
        import_tools

import_tools(["ctasks", "tpl_tasks", "cython", "fortran", "swig"], ["tools"])

def create_sources(bld, name, sources):
    tasks = create_tasks(bld, sources)
    run_tasks(bld, tasks)

if __name__ == "__main__":
    from yaku.tools.gcc import detect as gcc_detect
    from yaku.tools.gfortran import detect as gfortran_detect

    bld = get_bld()
    bld.env.update(get_pyenv())

    gcc_detect(bld)
    gfortran_detect(bld)
    bld.env.update({"CPPPATH": [], "LIBPATH": [], "LIBS": [],
            "SWIG": ["swig"],
            "SWIGFLAGS": ["-python"],
            "SUBST_DICT": {"VERSION": "0.0.2"},
            "VERBOSE": False,
            "BLDDIR": "build"})

    if "-v" in sys.argv:
        bld.env["VERBOSE"] = True
    #from pprint import pprint
    #pprint(bld.env)

    create_sources(bld, "template", sources=["src/foo.h.in"])
    create_pyext(bld, "_bar", ["src/hellomodule.c", "src/foo.c"])
    create_pyext(bld, "_von", ["src/vonmises_cython.pyx"])
    create_pyext(bld, "_fortran_yo", ["src/bar.f"])
    create_pyext(bld, "_swig_yo", ["src/yo.i"])

    with open(CACHE_FILE, "w") as fid:
        dump(bld.cache, fid)
