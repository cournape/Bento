from yaku.scheduler \
    import \
        run_tasks
from yaku.context \
    import \
        get_bld, get_cfg
from yaku.conftests \
    import \
        check_func, check_header, check_compiler, check_cpp_symbol

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

    assert check_func(ctx, "malloc")
    assert not check_func(ctx, "mmalloc")

    assert check_header(ctx, "stdio.h")
    assert not check_header(ctx, "stdioo.h")

    assert check_compiler(ctx)
    assert check_cpp_symbol(ctx, "NULL", ["stdio.h"])
    assert not check_cpp_symbol(ctx, "VERY_UNLIKELY_SYMOBOL_@aqwhn")

if __name__ == "__main__":
    ctx = get_cfg()
    configure(ctx)
    ctx.store()
