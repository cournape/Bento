import sys
import os

from yaku.task_manager \
    import \
        create_tasks
from yaku.scheduler \
    import \
        run_tasks
from yaku.context \
    import \
        get_bld, get_cfg
import yaku.node
import yaku.errors

def configure(ctx):
    import numpy.distutils
    ctx.use_tools(["pyext", "ctasks", "cxxtasks", "tpl_tasks", "fortran"],
                  ["tools"])
    try:
        ctx.use_tools(["cython"])
    except yaku.errors.ToolNotFound:
        raise RuntimeError("Cython not found - please install Cython!")
    ctx.env.update({"SUBST_DICT": {"VERSION": "0.0.2"}})
    for p in numpy.distutils.misc_util.get_numpy_include_dirs()[::-1]:
        ctx.env["PYEXT_CPPPATH"].insert(0, p)

def build(ctx):
    #pyext = ctx.builders["pyext"]
    #pyext.extension("_bar", [os.path.join("src", f) for f in ["hellomodule.c", "foo.c"]])
    #pyext.extension("_von", [os.path.join("src/vonmises_cython.pyx")])
    #ctx.builders["tpl_tasks"].build("template", sources=[os.path.join("src", "foo.h.in")])

    builder = ctx.builders["cxxtasks"]
    builder.program("foo", ["src/main.cxx"])

if __name__ == "__main__":
    ctx = get_cfg()
    configure(ctx)
    ctx.store()

    ctx = get_bld()
    build(ctx)
    run_tasks(ctx)
    ctx.store()
