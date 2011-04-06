import yaku.tools

from yaku.task \
    import \
        task_factory
from yaku.task_manager \
    import \
        extension, TaskGen

def render(task):
    import jinja2
    content = task.inputs[0].read()
    template = jinja2.Template(content)
    task.outputs[0].write(template.render(**task.env["SUBST_DICT"]))

@extension(".in")
def template_task(task_gen, node):
    out = node.change_ext("")
    target = node.parent.declare(out.name)
    task = task_factory("subst")(inputs=[node], outputs=[target], func=render)
    task.env_vars = ["SUBST_DICT"]
    task.env = task_gen.env
    return [task]

class TemplateBuilder(yaku.tools.Builder):
    def render(self, sources, vars=None):
        if vars is None:
            self.env["SUBST_DICT"]  = {}
        else:
            self.env["SUBST_DICT"]  = vars
        return self._task_gen_factory("subst", "noname", sources, None)

def get_builder(context):
    return TemplateBuilder(context)
