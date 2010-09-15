import re
import os
import copy

from yaku.pprint \
    import \
        pprint
from yaku.task \
    import \
        Task
from yaku.task_manager \
    import \
        extension
from yaku.utils \
    import \
        ensure_dir

VARS = {"template": ["SUBST_DICT"]}

def template(self):
    if not len(self.inputs) == 1:
        raise ValueError("template func needs exactly one input")

    pprint('GREEN', "%-16s%s" % (self.name.upper(),
        " ".join([str(s) for s in self.inputs])))
    subs_re = dict([(k, re.compile("@" + k + "@")) 
                     for k in self.env["SUBST_DICT"]])
    cnt = self.inputs[0].read()
    for k, v in self.env["SUBST_DICT"].items():
        cnt = subs_re[k].sub(v, cnt)

    ensure_dir(self.outputs[0].abspath())
    self.outputs[0].write(cnt)

@extension(".in")
def template_task(self, node):
    out = node.change_ext("")
    target = node.parent.declare(out.name)
    task = Task("template", inputs=[node], outputs=[target])
    task.func = template
    task.env_vars = VARS["template"]
    task.env = self.env
    return [task]

class TemplateBuilder(object):
    def __init__(self, ctx):
        self.ctx = ctx
        self.env = copy.deepcopy(ctx.env)

    def build(self, name, sources, env=None):
        sources = [self.ctx.src_root.find_resource(s) for s in sources]
        _env = copy.deepcopy(self.env)
        if env is not None:
            _env.update(env)

        task_gen = CompiledTaskGen("template", self.ctx,
                                   sources, name)
        tasks = task_gen.process()
        self.ctx.tasks.extend(tasks)

        outputs = tasks[0].outputs[:]
        return outputs

def get_builder(ctx):
    return TemplateBuilder(ctx)
