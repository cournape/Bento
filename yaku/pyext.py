import os
import copy

from utils \
    import \
        ensure_dir
from task \
    import \
        Task
from task_manager \
    import \
        create_tasks, topo_sort, build_dag, run_tasks, CompiledTaskGen, set_extension_hook
from compiled_fun \
    import \
        compile_fun

def apply_cpppath(task_gen):
    cpppaths = task_gen.env["CPPPATH"]
    cpppaths.extend(task_gen.env["PYEXT_CPPPATH"])
    implicit_paths = set([
        os.path.join(task_gen.env["BLDDIR"], os.path.dirname(s))
        for s in task_gen.sources])
    cpppaths = list(implicit_paths) + cpppaths
    task_gen.env["PYEXT_INCPATH"] = [
            task_gen.env["PYEXT_INCPATH_FMT"] % p
            for p in cpppaths]

def order_tasks(tasks):
    tuid_to_task = dict([(t.get_uid(), t) for t in tasks])

    task_deps, output_to_tuid = build_dag(tasks)

    yo = topo_sort(task_deps)
    ordered_tasks = []
    for output in yo:
        if output in output_to_tuid:
            ordered_tasks.append(tuid_to_task[output_to_tuid[output]])

    return ordered_tasks

pylink, pylink_vars = compile_fun("pylink", "${PYEXT_SHLINK} -o ${TGT[0]} ${SRC}", False)

pycc, pycc_vars = compile_fun("pycc", "${PYEXT_SHCC} ${PYEXT_CCSHARED} ${PYEXT_CFLAGS} ${PYEXT_INCPATH} -o ${TGT[0]} -c ${SRC}", False)

def pycc_hook(self, node):
    tasks = pycc_task(self, node)
    self.object_tasks.extend(tasks)
    return tasks

def pycc_task(self, node):
    base = os.path.splitext(node)[0]
    # XXX: hack to avoid creating build/build/... when source is
    # generated. Dealing with this most likely requires a node concept
    if not os.path.commonprefix([self.env["BLDDIR"], base]):
        target = os.path.join(self.env["BLDDIR"], base + ".o")
    else:
        target = base + ".o"
    ensure_dir(target)
    task = Task("pycc", inputs=node, outputs=target)
    task.env_vars = pycc_vars
    task.env = self.env
    task.func = pycc
    return [task]

def pylink_task(self, name):
    objects = [tsk.outputs[0] for tsk in self.object_tasks]
    target = os.path.join(self.env["BLDDIR"], name + ".so")
    ensure_dir(target)
    task = Task("pylink", inputs=objects, outputs=target)
    task.func = pylink
    task.env_vars = pylink_vars
    return [task]

def create_pyext(bld, name, sources):
    base = name.split(".")[-1]

    tasks = []

    task_gen = CompiledTaskGen("pyext", sources, name)
    old_hook = set_extension_hook(".c", pycc_hook)

    task_gen.env.update(copy.deepcopy(bld.env))
    apply_cpppath(task_gen)

    tasks = create_tasks(task_gen, sources)

    ltask = pylink_task(task_gen, name.split(".")[-1])
    tasks.extend(ltask)
    for t in tasks:
        t.env = task_gen.env

    ordered_tasks = order_tasks(tasks)
    run_tasks(bld, ordered_tasks)

    set_extension_hook(".c", old_hook)
