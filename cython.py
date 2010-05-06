import os

from ctasks \
    import \
        ccompile_task
from task_manager \
    import \
        extension
from task \
    import \
        Task
from compiled_fun \
    import \
        compile_fun

@extension(".pyx")
def cython_task(self, node):
    base = os.path.splitext(node)[0]
    target = base + ".c"
    task = Task("cython", inputs=node, outputs=target)
    task.env_vars = []
    task.env = self.env
    task.func = compile_fun("cython", "cython ${SRC}", False)[0]
    ctask = ccompile_task(self, target)
    self.object_tasks.extend(ctask)
    return [task] + ctask
