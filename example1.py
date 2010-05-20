import sys

from yaku.pyext \
    import \
        create_pyext, get_pyenv

from yaku.build_context \
    import \
        get_bld
from yaku.tools \
    import \
        import_tools

from yaku.tools.gcc import detect as gcc_detect

# Use dot in the name to avoid accidental import of it
CONFIG_INFO = "default.config.py"

def configure(ctx):
    import_tools(["ctasks"], ["tools"])

    if "-v" in sys.argv:
        ctx.env["VERBOSE"] = True
    gcc_detect(ctx)
    ctx.env.update(get_pyenv())

def build(ctx):
    create_pyext(bld, "_bar", ["src/hellomodule.c"])

if __name__ == "__main__":
    bld = get_bld()
    configure(bld)
    build(bld)
    bld.save()
