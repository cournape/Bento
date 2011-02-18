import os
import sys

from yaku.scheduler \
    import \
        run_tasks
from yaku.context \
    import \
        get_bld, get_cfg
import yaku.tools

def configure(conf):
    ctx.load_tool("python_2to3")

def build(ctx):
    builder = ctx.builders["python_2to3"]
    files = []
    for r, ds, fs in os.walk("foo"):
        files.extend([os.path.join(r, f) for f in fs])
    builder.convert("", files)

if __name__ == "__main__":
    ctx = get_cfg()
    configure(ctx)
    ctx.setup_tools()
    ctx.store()

    ctx = get_bld()
    build(ctx)
    try:
        run_tasks(ctx)
    finally:
        ctx.store()
