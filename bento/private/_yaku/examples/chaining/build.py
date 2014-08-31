import sys
import os

from yaku.task_manager \
    import \
        set_extension_hook, get_extension_hook
from yaku.scheduler \
    import \
        run_tasks
from yaku.context \
    import \
        get_bld, get_cfg
import yaku.node
import yaku.errors

def configure(ctx):
    ctx.use_tools(["ctasks", "pyext", "template"])
    try:
        ctx.use_tools(["cython"])
    except yaku.errors.ToolNotFound:
        raise RuntimeError("Cython not found - please install Cython!")
    ctx.env.update({"SUBST_DICT": {"VERSION": "0.0.2"}})

def build(ctx):
    pyext = ctx.builders["pyext"]

    old_hook = get_extension_hook(".in")
    def foo(self, node):
        recursive_suffixes = [".c", ".cxx", ".pyx"]
        out = node.change_ext("")
        # XXX: is it really safe to items to a list one recurses on ?
        if out.suffix() in recursive_suffixes:
            self.sources.append(out)
        return old_hook(self, node)
    set_extension_hook(".in", foo)

    pyext.extension("hello", ["hello.pyx.in"])

if __name__ == "__main__":
    ctx = get_cfg()
    configure(ctx)
    ctx.store()

    ctx = get_bld()
    build(ctx)
    run_tasks(ctx)
    ctx.store()
