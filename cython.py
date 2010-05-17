import os

from task_manager \
    import \
        extension, get_extension_hook
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
    compile_task = get_extension_hook(".c")
    ctask = compile_task(self, target)
    return [task] + ctask
