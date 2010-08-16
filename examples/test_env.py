import sys
import os
import copy

from yaku.context \
    import \
        get_bld, get_cfg
from yaku.scheduler \
    import \
        run_tasks

def configure(ctx):
    ctx.use_tools(["ctasks"])

def build(ctx):
    # To *override* options, you should clone a builder + replacing
    # options there
    builder = ctx.builders["ctasks"].clone()
    builder.env["CFLAGS"] = ["-g", "-DNDEBUG"]
    builder.program("main", sources=["src/main.c"], env={"CFLAGS": ["-O2"]})
    builder.program("main2", sources=["src/main2.c"])

    # env argument to methods *add* option - note that main3.c is not
    # built with -g nor -DNDEBUG
    program = ctx.builders["ctasks"].program
    program("main2", sources=["src/main3.c"], env={"CFLAGS": ["-Os"]})

if __name__ == "__main__":
    ctx = get_cfg()
    configure(ctx)
    ctx.store()

    ctx = get_bld()
    build(ctx)
    run_tasks(ctx)
    ctx.store()
