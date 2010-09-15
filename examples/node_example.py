import os

from yaku.node import Node as _Node
from yaku.context import get_cfg, get_bld
from yaku.scheduler import run_tasks

class FakeContext(object): pass

if __name__ == "__main__":
    blddir = os.path.join("build")
    if not os.path.exists(blddir):
        os.makedirs(blddir)

    #ctx = FakeContext()
    class Node(_Node):
        ctx = FakeContext()
    root = Node("", None)

    start_dir = os.path.abspath(os.getcwd())
    start = root.find_dir(start_dir)
    bldnode = start.find_dir(blddir)
    Node.ctx.srcnode = start
    Node.ctx.bldnode = bldnode

    ctx = get_cfg()
    for t in ["cython", "pyext", "ctasks"]:
        ctx.load_tool(t)
    ctx.setup_tools()
    ctx.store()

    bld = get_bld()
    bld.src_root = start
    bld.bld_root = bldnode
    pyext = bld.builders["pyext"]
    pyext.extension("_foo", ["src/bar.pyx"])
    run_tasks(bld)
    bld.store()
