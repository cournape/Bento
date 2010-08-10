import os
import copy

from yaku.task_manager \
    import \
        extension, CompiledTaskGen, create_tasks
from yaku.task \
    import \
        Task
from yaku.compiled_fun \
    import \
        compile_fun
from yaku.utils \
    import \
        ensure_dir

f77_compile, f77_vars = compile_fun("f77", "${F77} ${F77FLAGS} ${F77_TGT_F}${TGT[0].abspath()} ${F77_SRC_F}${SRC}", False)

fprogram, fprogram_vars = compile_fun("fprogram", "${F77_LINK} ${F77_LINK_TGT_F}${TGT[0].abspath()} ${F77_LINK_SRC_F}${SRC}", False)

@extension(".f")
def fortran_task(self, node):
    tasks = fcompile_task(self, node)
    return tasks

def fcompile_task(self, node):
    folder, base = os.path.split(node.bld_base())
    tmp = folder + os.path.sep + "%s.o" % base
    target = node.ctx.bldnode.declare(tmp)
    ensure_dir(target.abspath())

    task = Task("f77", inputs=[node], outputs=[target])
    task.gen = self
    task.env_vars = f77_vars
    task.env = self.env
    task.func = f77_compile
    self.object_tasks.append(task)
    return [task]

def configure(ctx):
    cc = ctx.load_tool("gfortran")
    cc.setup(ctx)

class FortranBuilder(object):
    def __init__(self, ctx):
        self.ctx = ctx
        self.env = copy.deepcopy(ctx.env)

    def ccompile(self, name, sources, env=None):
        _env = copy.deepcopy(self.env)
        if env is not None:
            _env.update(env)

        task_gen = CompiledTaskGen("cccompile", sources, name)
        task_gen.bld = self.ctx
        task_gen.env = _env
        apply_cpppath(task_gen)

        tasks = create_tasks(task_gen, sources)
        for t in tasks:
            t.env = task_gen.env
        self.ctx.tasks.extend(tasks)

        outputs = []
        for t in tasks:
            outputs.extend(t.outputs)
        return outputs

    def program(self, name, sources, env=None):
        _env = copy.deepcopy(self.env)
        if env is not None:
            _env.update(env)

        sources = [self.ctx.src_root.find_resource(s) for s in sources]
        task_gen = CompiledTaskGen("fprogram", sources, name)
        task_gen.env = _env
        task_gen.bld = self.ctx

        tasks = create_tasks(task_gen, sources)
        ltask = fprogram_task(task_gen, name)
        tasks.extend(ltask)
        for t in tasks:
            t.env = task_gen.env
        self.ctx.tasks.extend(tasks)

        outputs = []
        for t in ltask:
            outputs.extend(t.outputs)
        return outputs

def fprogram_task(self, name):
    objects = [tsk.outputs[0] for tsk in self.object_tasks]
    def declare_target():
        folder, base = os.path.split(name)
        tmp = folder + os.path.sep + self.env["F77_PROGRAM_FMT"] % base
        return self.bld.bld_root.declare(tmp)
    target = declare_target()
    ensure_dir(target.abspath())

    task = Task("fprogram", inputs=objects, outputs=[target])
    task.gen = self
    task.env = self.env
    task.func = fprogram
    task.env_vars = fprogram_vars
    return [task]

def get_builder(ctx):
    return FortranBuilder(ctx)
