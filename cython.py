import os

from pyext \
    import \
        pycc_task
from task_manager \
    import \
        extension
from task \
    import \
        Task
from compiled_fun \
    import \
        compile_fun
from utils \
    import \
        ensure_dir

@extension(".pyx")
def cython_task(self, node):
    base = os.path.splitext(node)[0]
    target = os.path.join(self.env["BLDDIR"], base + ".c")
    ensure_dir(target)
    task = Task("cython", inputs=node, outputs=target)
    task.env_vars = []
    task.env = self.env
    task.func = compile_fun("cython", "cython ${SRC} -o ${TGT}",
                            False)[0]
    ctask = pycc_task(self, target)
    self.object_tasks.extend(ctask)
    return [task] + ctask
