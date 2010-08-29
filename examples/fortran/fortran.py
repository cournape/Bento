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
    ctx.use_tools(["fortran"])

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
