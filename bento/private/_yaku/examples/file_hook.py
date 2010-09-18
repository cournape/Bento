import yaku.task_manager

from yaku.task_manager import get_extension_hook, set_file_hook
from yaku.context import get_cfg, get_bld
from yaku.scheduler import run_tasks

def file_hook(self, node):
    print "Yo mama", node.name
    return get_extension_hook(".c")(self, node)

def configure(ctx):
    ctx.use_tools(["ctasks"])
    set_file_hook(ctx, "src/fubar.c", file_hook)

def build(ctx):
    builder = ctx.builders["ctasks"].program
    builder("src/main", sources=["src/main.c", "src/fubar.c"])

if __name__ == "__main__":
    cfg = get_cfg()
    configure(cfg)
    cfg.store()

    bld = get_bld()
    build(bld)
    run_tasks(bld)
    bld.store()
