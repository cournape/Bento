import os
import subprocess

from toydist.core.utils \
    import \
        pprint

from task \
    import \
        Task
from task_manager \
    import \
        extension
from utils \
    import \
        find_deps, ensure_dir
from compiled_fun \
    import \
        compile_fun

VARS = {"cc": ["CC", "CFLAGS", "CPPPATH"],
        "cc_link": ["SHLINK", "SHLINKFLAGS"]}

ccompile = compile_fun("cc", "${CC} ${INCPATH} -o ${TGT[0]} -c ${SRC}", False)[0]

cshlink = compile_fun("cshlib", "${SHLINK} ${SHLINKFLAGS} -o ${TGT[0]} ${SRC}", False)[0]

@extension('.c')
def c_hook(self, node):
    tasks = ccompile_task(self, node)
    self.object_tasks.extend(tasks)
    return tasks

def ccompile_task(self, node):
    base = os.path.splitext(node)[0]
    # XXX: hack to avoid creating build/build/... when source is
    # generated. Dealing with this most likely requires a node concept
    if not os.path.commonprefix([self.env["BLDDIR"], base]):
        target = os.path.join(self.env["BLDDIR"], base + ".o")
    else:
        target = base + ".o"
    ensure_dir(target)
    task = Task("cc", inputs=node, outputs=target)
    task.env_vars = VARS["cc"]
    #print find_deps("foo.c", ["."])
    #task.scan = lambda : find_deps(node, ["."])
    #task.deps.extend(task.scan())
    task.env = self.env
    task.func = ccompile
    return [task]

def link_task(self, name):
    objects = [tsk.outputs[0] for tsk in self.object_tasks]
    target = os.path.join(self.env["BLDDIR"], name + ".so")
    ensure_dir(target)
    task = Task("cc_link", inputs=objects, outputs=target)
    task.func = cshlink
    task.env_vars = VARS["cc_link"]
    return [task]
