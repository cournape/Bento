import os

from yaku.task_manager \
    import \
        extension
from yaku.task \
    import \
        Task
from yaku.compiled_fun \
    import \
        compile_fun
from yaku.utils \
    import \
        ensure_dir

@extension(".f")
def fortran_task(self, node):
    base = os.path.splitext(node)[0]
    # XXX: hack to avoid creating build/build/... when source is
    # generated. Dealing with this most likely requires a node concept
    if not base.startswith(self.env["BLDDIR"]):
        target = os.path.join(self.env["BLDDIR"], base + ".o")
    else:
        target = base + ".o"
    ensure_dir(target)

    func, env_vars = compile_fun("f77",
            "${F77} ${F77FLAGS} -c ${SRC} -o ${TGT[0]}", False)
    task = Task("f77", inputs=node, outputs=target)
    task.env_vars = env_vars
    task.env = self.env
    task.func = func
    self.object_tasks.append(task)
    return [task]
