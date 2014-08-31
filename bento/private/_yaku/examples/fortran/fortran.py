from yaku.scheduler \
    import \
        run_tasks
from yaku.context \
    import \
        get_bld, get_cfg
import yaku.node
import yaku.errors

def configure(ctx):
    ctx.use_tools(["fortran", "ctasks"])
    assert ctx.builders["fortran"].try_compile("foo", """\
       program foo
       end
""")

    assert not ctx.builders["fortran"].try_compile("foo", """\
       pprogram foo
       end
""")

    assert ctx.builders["fortran"].try_program("foo", """\
       program foo
       end
""")

    assert not ctx.builders["fortran"].try_program("foo", """\
       pprogram foo
       end
""")

def build(ctx):
    builder = ctx.builders["fortran"]
    builder.program("fbar", ["src/bar.f"])

if __name__ == "__main__":
    ctx = get_cfg()
    configure(ctx)
    ctx.store()

    ctx = get_bld()
    build(ctx)
    run_tasks(ctx)
    ctx.store()
