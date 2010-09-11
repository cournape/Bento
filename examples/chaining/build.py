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
    ctx.use_tools(["pyext", "tpl_tasks"])
    try:
        ctx.use_tools(["cython"])
    except yaku.errors.ToolNotFound:
        raise RuntimeError("Cython not found - please install Cython!")
    ctx.env.update({"SUBST_DICT": {"VERSION": "0.0.2"}})

def build(ctx):
    pyext = ctx.builders["pyext"]
    pyext.extension("hello", ["hello.pyx.in"])

if __name__ == "__main__":
    ctx = get_cfg()
    configure(ctx)
    ctx.store()

    ctx = get_bld()
    build(ctx)
    run_tasks(ctx)
    ctx.store()
