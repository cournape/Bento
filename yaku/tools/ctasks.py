import os

from yaku.task \
    import \
        Task
from yaku.task_manager \
    import \
        extension
from yaku.utils \
    import \
        find_deps, ensure_dir
from yaku.compiled_fun \
    import \
        compile_fun

ccompile, cc_vars = compile_fun("cc", "${CC} ${CFLAGS} ${INCPATH} -o ${TGT[0]} -c ${SRC}", False)

cshlink, cshlink_vars = compile_fun("cshlib", "${SHLINK} ${SHLINKFLAGS} ${APP_LIBPATH} ${APP_LIBS} -o ${TGT[0]} ${SRC}", False)

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
    task.env_vars = cc_vars
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
    task.env = self.env
    task.func = cshlink
    task.env_vars = cshlink_vars
    return [task]

def apply_libs(task_gen):
    libs = task_gen.env["LIBS"]
    task_gen.env["APP_LIBS"] = [
            task_gen.env["LIBS_FMT"] % lib for lib in libs]

def apply_libpath(task_gen):
    libdir = task_gen.env["LIBPATH"]
    implicit_paths = set([
        os.path.join(task_gen.env["BLDDIR"], os.path.dirname(s))
        for s in task_gen.sources])
    libdir = list(implicit_paths) + libdir
    task_gen.env["APP_LIBPATH"] = [
            task_gen.env["LIBPATH_FMT"] % d for d in libdir]
