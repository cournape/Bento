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
    task = Task("f77", inputs=node, outputs=target)
    task.env_vars = ["F77", "F77FLAGS"]
    task.env = self.env
    task.func = compile_fun("f77", "${F77} -c ${SRC} -o ${TGT[0]}",
                            False)[0]
    self.object_tasks.append(task)
    return [task]
