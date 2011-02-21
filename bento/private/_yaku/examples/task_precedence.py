import sys
import os

from yaku.context \
    import \
        get_bld, get_cfg
from yaku.scheduler \
    import \
        run_tasks
from yaku.task \
    import \
        task_factory

import yaku.tools
import yaku.errors

from yaku.pprint import pprint

# Hack to track we run all copy tasks before any convert one
__RUN_CONVERT = False

def copy_func(self):
    if __RUN_CONVERT:
        raise AssertionError("precendence test failed")
    source, target = self.inputs[0], self.outputs[0]
    pprint('BLUE', "%-16s%s" % (self.name.upper(), self.inputs[0].srcpath()))
    target.write(source.read())

def convert_func(self):
    global __RUN_CONVERT
    __RUN_CONVERT = True
    source, target = self.inputs[0], self.outputs[0]
    pprint('BLUE', "%-16s%s" % (self.name.upper(), self.inputs[0].srcpath()))
    target.write("")

class DummyBuilder(yaku.tools.Builder):
    def __init__(self, ctx):
        super(DummyBuilder, self).__init__(ctx)

    def build(self, sources, env=None):
        sources = [self.ctx.src_root.find_resource(s) for s in sources]
        #task_gen = TaskGen("dummy", self.ctx, sources, name)
        env = yaku.tools._merge_env(self.env, env)

        copy_tf = task_factory("convert_copy")
        convert_tf = task_factory("convert_do")
        convert_tf.before.append(copy_tf.__name__)

        py3k_tmp = self.ctx.bld_root.declare("_py3k")
        tasks = []
        for source in sources:
            target = py3k_tmp.declare(source.srcpath())
            task = copy_tf([target], [source])
            task.func = copy_func
            task.env_vars = {}
            tasks.append(task)

            source = target
            target = self.ctx.bld_root.declare(source.srcpath())
            task = convert_tf([target], [source])
            task.func = convert_func
            task.env_vars = {}
            tasks.append(task)

        for t in tasks:
            t.env = env
        self.ctx.tasks.extend(tasks)

        return []

def configure(ctx):
    pass
    #ctx.builders["dummy"] = DummyBuilder(ctx)

def build(ctx):
    blder = DummyBuilder(ctx)
    files = []
    for r, ds, fs in os.walk("."):
        for f in fs:
            if f.endswith(".py"):
                files.append(os.path.join(r, f))
    blder.build(files)

if __name__ == "__main__":
    ctx = get_cfg()
    configure(ctx)
    ctx.setup_tools()
    ctx.store()

    ctx = get_bld()
    build(ctx)
    tasks = ctx.tasks
    run_tasks(ctx)
    ctx.store()
