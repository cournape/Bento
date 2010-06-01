import os
import sys

from yaku.pyext \
    import \
        create_pyext, get_pyenv
from yaku.context \
    import \
        get_bld, get_cfg

# FIXME: should be done dynamically
from yaku.tools.gcc \
    import \
        detect as gcc_detect

from yaku.conftests \
    import \
        check_compiler, check_header

def configure(ctx):
    ctx.use_tools(["ctasks"], ["tools"])

    gcc_detect(ctx)
    check_compiler(ctx)
    check_header(ctx, "stdio.h")
    ctx.env.update(get_pyenv())

def build(ctx):
    create_pyext(ctx, "_bar", ["src/hellomodule.c"])

if __name__ == "__main__":
    ctx = get_cfg()
    configure(ctx)
    ctx.store()

    ctx = get_bld()
    build(ctx)
    ctx.store()
