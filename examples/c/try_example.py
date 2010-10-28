from yaku.scheduler \
    import \
        run_tasks
from yaku.context \
    import \
        get_bld, get_cfg

def configure(ctx):
    ctx.use_tools(["ctasks", "cxxtasks"])
    ctx.env.append("DEFINES", "_FOO")

    cc = ctx.builders["ctasks"]
    assert cc.try_compile("foo", "int main() {}")
    assert not cc.try_compile("foo", "intt main() {}")

    assert cc.try_program("foo", "int main() {}")
    assert not cc.try_program("foo", "intt main() {}")

    assert cc.try_static_library("foo", "int foo() {}")
    assert not cc.try_static_library("foo", "intt foo() {}")

if __name__ == "__main__":
    ctx = get_cfg()
    configure(ctx)
    ctx.store()
