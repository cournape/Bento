import re
import os

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

    pprint('GREEN', "%-16s%s" % (self.name.upper(), " ".join(self.inputs)))
    subs_re = dict([(k, re.compile("@" + k + "@")) 
                     for k in self.env["SUBST_DICT"]])
    fid = open(self.inputs[0])
    try:
        cnt = fid.read()
        for k, v in self.env["SUBST_DICT"].items():
            cnt = subs_re[k].sub(v, cnt)
    finally:
        fid.close()

    ensure_dir(self.outputs[0])
    fid = open(self.outputs[0], "w")
    try:
        fid.write(cnt)
    finally:
        fid.close()

@extension(".in")
def template_task(self, node):
    base = os.path.splitext(node)[0]
    target = os.path.join(self.env["BLDDIR"], base)
    task = Task("template", inputs=node, outputs=target)
    task.func = template
    task.env_vars = VARS["template"]
    task.env = self.env
    return [task]
