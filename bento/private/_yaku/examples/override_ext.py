import sys
import os
import copy

from yaku.context \
    import \
        get_bld, get_cfg
from yaku.scheduler \
    import \
        run_tasks
from yaku.task_manager \
    import \
        get_extension_hook, set_file_hook, set_extension_hook, \
        wrap_extension_hook

def configure(ctx):
    ctx.use_tools(["ctasks"])

# A hook wrapper takes the existing hook as an argument, and returns
# the new hook (callable).
def custom_c_hooker(c_hook):
    # Dummy hook printing the node name
    def hook(ctx, node):
        print("Compiling file: %s, with flags %s" % \
                (node.name, " ".join(ctx.env["CFLAGS"])))
        return c_hook(ctx, node)
    return hook

def build(ctx):
    program = ctx.builders["ctasks"].program
    c_hook = wrap_extension_hook(".c", custom_c_hooker)
    try:
        program("main1", sources=["src/main.c"])
    finally:
        set_extension_hook(".c", c_hook)
    program("main2", sources=["src/main2.c"])

if __name__ == "__main__":
    ctx = get_cfg()
    configure(ctx)
    ctx.store()

    ctx = get_bld()
    build(ctx)
    run_tasks(ctx)
    ctx.store()
