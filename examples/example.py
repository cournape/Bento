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
import yaku.errors

def configure(ctx):
    ctx.use_tools(["pyext", "ctasks", "tpl_tasks",
                   "fortran", "swig"], ["tools"])
    try:
        ctx.use_tools(["cython"])
    except yaku.errors.ToolNotFound:
        raise RuntimeError("Cython not found - please install Cython!")
    ctx.env.update({
            #"SWIG": ["swig"],
            #"SWIGFLAGS": ["-python"],
            "SUBST_DICT": {"VERSION": "0.0.2"}})

def build(ctx):
    pyext = ctx.builders["pyext"]
    create_sources(ctx, "template", sources=[os.path.join("src", "foo.h.in")])
    pyext.extension("_bar", [os.path.join("src", f) for f in ["hellomodule.c", "foo.c"]])
    pyext.extension("_von", [os.path.join("src/vonmises_cython.pyx")])
    #create_pyext(ctx, "_fortran_yo", ["src/bar.f"])
    #create_pyext(ctx, "_swig_yo", ["src/yo.i"])

def create_sources(ctx, name, sources):
    tasks = create_tasks(ctx, sources)
    run_tasks(ctx, tasks)

if __name__ == "__main__":
    ctx = get_cfg()
    configure(ctx)
    ctx.store()

    ctx = get_bld()
    build(ctx)
    run_tasks(ctx)
    ctx.store()
