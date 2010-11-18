import re
import os
import copy

from yaku.pprint \
    import \
        pprint
from yaku.task \
    import \
        task_factory
from yaku.task_manager \
    import \
        extension, TaskGen
from yaku.utils \
    import \
        ensure_dir
import yaku.tools

VARS = {"template": ["SUBST_DICT"]}

def _escape_backslash(s):
    return s.replace("\\", "\\\\")

def _render(content, d):
    subs_re = dict([(k, re.compile("@%s@" % k)) for k in d])
    for k, v in d.items():
        # we cannot use re.escape because it escapes slash as well
        content = subs_re[k].sub(_escape_backslash(v), content)
    return content

def template(self):
    if not len(self.inputs) == 1:
        raise ValueError("template func needs exactly one input")

    pprint('GREEN', "%-16s%s" % (self.name.upper(),
        " ".join([str(s) for s in self.inputs])))
    content = self.inputs[0].read()
    content = _render(content, self.env["SUBST_DICT"])
    ensure_dir(self.outputs[0].abspath())
    self.outputs[0].write(content)

@extension(".in")
def template_task(self, node):
    out = node.change_ext("")
    target = node.parent.declare(out.name)
    task = task_factory("template")(inputs=[node], outputs=[target])
    task.func = template
    task.env_vars = VARS["template"]
    task.env = self.env
    return [task]

class TemplateBuilder(yaku.tools.Builder):
    def __init__(self, ctx):
        yaku.tools.Builder.__init__(self, ctx)

    def build(self, name, sources, env=None):
        sources = [self.ctx.src_root.find_resource(s) for s in sources]
        task_gen = TaskGen("template", self.ctx, sources, name)
        task_gen.env = yaku.tools._merge_env(self.env, env)
        tasks = task_gen.process()
        for t in tasks:
            t.env = task_gen.env
        self.ctx.tasks.extend(tasks)

        outputs = tasks[0].outputs[:]
        return outputs

def get_builder(ctx):
    return TemplateBuilder(ctx)
