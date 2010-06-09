import sys

from yaku.task_manager \
    import \
        create_tasks
from yaku.scheduler \
    import \
        run_tasks
from yaku.context \
    import \
        get_bld, get_cfg

from yaku.tools.gcc import detect as gcc_detect
from yaku.tools.gfortran import detect as gfortran_detect

def configure(ctx):
    ctx.use_tools(["pyext", "ctasks", "tpl_tasks", "cython",
                   "fortran", "swig"], ["tools"])
    ctx.env.update({
            #"SWIG": ["swig"],
            #"SWIGFLAGS": ["-python"],
            "SUBST_DICT": {"VERSION": "0.0.2"}})

    gcc_detect(ctx)
    gfortran_detect(ctx)

def build(ctx):
    pyext = ctx.builders["pyext"]
    create_sources(ctx, "template", sources=["src/foo.h.in"])
    pyext.extension("_bar", ["src/hellomodule.c", "src/foo.c"])
    pyext.extension("_von", ["src/vonmises_cython.pyx"])
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
