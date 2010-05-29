import sys

from yaku.pyext \
    import \
        create_pyext, get_pyenv
from yaku.task_manager \
    import \
        create_tasks, run_tasks
from yaku.context \
    import \
        get_bld, get_cfg

from yaku.tools.gcc import detect as gcc_detect
from yaku.tools.gfortran import detect as gfortran_detect

def configure(ctx):
    ctx.load_tools(["ctasks", "tpl_tasks", "cython",
                    "fortran", "swig"], ["tools"])
    ctx.env.update({
            #"SWIG": ["swig"],
            #"SWIGFLAGS": ["-python"],
            "SUBST_DICT": {"VERSION": "0.0.2"}})
    ctx.env.update(get_pyenv())

    gcc_detect(ctx)
    gfortran_detect(ctx)

def build(ctx):
    create_sources(ctx, "template", sources=["src/foo.h.in"])
    create_pyext(ctx, "_bar", ["src/hellomodule.c", "src/foo.c"])
    create_pyext(ctx, "_von", ["src/vonmises_cython.pyx"])
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
    ctx.store()
