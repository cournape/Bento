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

@extension(".f")
def fortran_task(self, node):
    base = os.path.splitext(node)[0]
    target = base + ".o"
    task = Task("f77", inputs=node, outputs=target)
    task.env_vars = ["F77", "F77FLAGS"]
    task.env = self.env
    task.func = compile_fun("f77", "${F77} -c ${SRC} -o ${TGT[0]}",
                            False)[0]
    self.object_tasks.append(task)
    return [task]

