import sys

from yaku.scheduler \
    import \
        run_tasks
from yaku.context \
    import \
        get_bld, get_cfg

from yaku.conftests.fconftests \
    import \
        check_fcompiler, check_fortran_verbose_flag, \
        check_fortran_runtime_flags, check_fortran_dummy_main, \
        check_fortran_mangling

def configure(ctx):
    ctx.use_tools(["ctasks", "cxxtasks"])
    ctx.load_tool("fortran")
    ctx.builders["fortran"].configure(candidates=["gfortran"])

    check_fcompiler(ctx)
    check_fortran_verbose_flag(ctx)
    check_fortran_runtime_flags(ctx)
    check_fortran_dummy_main(ctx)
    check_fortran_mangling(ctx)

def build(ctx):
    builder = ctx.builders["fortran"]
    builder.program("fbar", ["src/bar.f"])

    builder = ctx.builders["ctasks"]
    builder.program("cbar", ["src/bar.c"])

    builder = ctx.builders["cxxtasks"]
    builder.program("cxxbar", ["src/bar.cxx"])

if __name__ == "__main__":
    ctx = get_cfg()
    configure(ctx)
    ctx.store()

    ctx = get_bld()
    build(ctx)
    run_tasks(ctx)
    ctx.store()
