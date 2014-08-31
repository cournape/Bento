from yaku.scheduler \
    import \
        run_tasks
from yaku.context \
    import \
        get_bld, get_cfg

def configure(ctx):
    ctx.use_tools(["ctasks", "cxxtasks"])
    ctx.env.append("DEFINES", "_FOO")

def build(ctx):
    builder = ctx.builders["cxxtasks"]
    builder.program("foo", ["src/main.cxx"])

    builder = ctx.builders["ctasks"]
    builder.static_library("bar", ["src/bar.c"])

if __name__ == "__main__":
    build_path = "BBUILD"
    ctx = get_cfg(build_path=build_path)
    configure(ctx)
    ctx.store()

    ctx = get_bld(build_path=build_path)
    build(ctx)
    run_tasks(ctx)
    ctx.store()
