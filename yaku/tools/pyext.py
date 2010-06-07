import os
import copy
import distutils

from yaku.task_manager \
    import \
        create_tasks, topo_sort, build_dag, \
        CompiledTaskGen, set_extension_hook
from yaku.sysconfig \
    import \
        get_configuration
from yaku.compiled_fun \
    import \
        compile_fun
from yaku.task \
    import \
        Task
from yaku.utils \
    import \
        ensure_dir
# FIXME: should be done dynamically
from yaku.tools.gcc \
    import \
        detect as gcc_detect
from yaku.conftests \
    import \
        check_compiler, check_header

pylink, pylink_vars = compile_fun("pylink", "${PYEXT_SHLINK} ${PYEXT_SHLINKFLAGS} ${PYEXT_APP_LIBDIR} ${PYEXT_APP_LIBS} -o ${TGT[0]} ${SRC}", False)

pycc, pycc_vars = compile_fun("pycc", "${PYEXT_SHCC} ${PYEXT_CCSHARED} ${PYEXT_CFLAGS} ${PYEXT_INCPATH} -o ${TGT[0]} -c ${SRC}", False)

_SYS_TO_PYENV = {
        "PYEXT_SHCC": "CC",
        "PYEXT_CCSHARED": "CCSHARED",
        "PYEXT_SHLINK": "LDSHARED",
        "PYEXT_SO": "SO",
        "PYEXT_CFLAGS": "CFLAGS",
        "PYEXT_OPT": "OPT",
        "PYEXT_LIBS": "LIBS",
        "PYEXT_INCPATH_FMT": "INCPATH_FMT",
}

def get_pyenv():
    sysenv = get_configuration()
    pyenv = {}
    for i, j in _SYS_TO_PYENV.items():
        pyenv[i] = sysenv[j]
    pyenv["PYEXT_CPPPATH"] = [distutils.sysconfig.get_python_inc()]
    pyenv["PYEXT_SHLINKFLAGS"] = []
    return pyenv

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

class PythonBuilder(object):
    def __init__(self, ctx):
        self.ctx = ctx
        self.env = copy.deepcopy(ctx.env)

    def extension(self, name, sources, env=None):
        _env = copy.deepcopy(self.env)
        if env is not None:
            _env.update(env)
        return create_pyext(self.ctx, _env, name, sources)

def get_builder(ctx):
    return PythonBuilder(ctx)

def configure(ctx):
    gcc_detect(ctx)
    check_compiler(ctx)

    ctx.env.update(get_pyenv())

def create_pyext(bld, env, name, sources):
    base = name.replace(".", os.sep)

    tasks = []

    task_gen = CompiledTaskGen("pyext", sources, name)
    old_hook = set_extension_hook(".c", pycc_hook)

    task_gen.env = env
    apply_cpppath(task_gen)
    apply_libpath(task_gen)
    apply_libs(task_gen)

    tasks = create_tasks(task_gen, sources)

    ltask = pylink_task(task_gen, base)
    tasks.extend(ltask)
    for t in tasks:
        t.env = task_gen.env

    set_extension_hook(".c", old_hook)
    bld.tasks.extend(tasks)

    outputs = []
    for t in ltask:
        outputs.extend(t.outputs)
    return outputs

# FIXME: find a way to reuse this kind of code between tools
def apply_libs(task_gen):
    libs = task_gen.env["LIBS"]
    task_gen.env["PYEXT_APP_LIBS"] = [
            task_gen.env["LIBS_FMT"] % lib for lib in libs]

def apply_libpath(task_gen):
    libdir = task_gen.env["LIBDIR"]
    implicit_paths = set([
        os.path.join(task_gen.env["BLDDIR"], os.path.dirname(s))
        for s in task_gen.sources])
    libdir = list(implicit_paths) + libdir
    task_gen.env["PYEXT_APP_LIBDIR"] = [
            task_gen.env["LIBDIR_FMT"] % d for d in libdir]

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
