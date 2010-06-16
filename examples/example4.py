import os
import sys

from yaku.context \
    import \
        get_bld, get_cfg
from yaku.scheduler \
    import \
        run_tasks

def configure(ctx):
    from yaku.sysconfig import detect_distutils_cc
    tools = ctx.use_tools(["ctasks"])
    # XXX: we have to use this until we have a detection framework
    cc = detect_distutils_cc(ctx)
    if sys.platform == "win32":
        import yaku.tools.msvc as msvc
        msvc.detect(ctx)
    else:
        import yaku.tools.gcc as gcc
        gcc.detect(ctx)

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
