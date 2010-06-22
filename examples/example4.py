import os
import sys

from yaku.context \
    import \
        get_bld, get_cfg
from yaku.scheduler \
    import \
        run_tasks

def configure(ctx):
    # The tool ctask works as follows:
    # - When a tool is *loaded* (load_tool), get its configure function (dummy
    # is setup if no configure is found)
    # - When a tool is *used* (use_tool), run its configure function
    # - given a list of candidates, run the detect function for every candidate
    # until detect returns True
    # - if one candidate found, record its name and run its setup function
    # - if none found, fails
    tools = ctx.use_tools(["ctasks"])

def build(ctx):
    builder = ctx.builders["ctasks"]
    builder.program("main", [os.path.join("src", "main.c")])

if __name__ == "__main__":
    ctx = get_cfg()
    configure(ctx)
    ctx.store()

    ctx = get_bld()
    build(ctx)
    run_tasks(ctx)
    ctx.store()
