import os
import copy

from yaku.task_manager \
    import \
        extension, CompiledTaskGen
from yaku.task \
    import \
        task_factory
from yaku.compiled_fun \
    import \
        compile_fun
from yaku.utils \
    import \
        ensure_dir
import yaku.tools

f77_compile, f77_vars = compile_fun("f77", "${F77} ${F77FLAGS} ${F77_TGT_F}${TGT[0].abspath()} ${F77_SRC_F}${SRC}", False)

fprogram, fprogram_vars = compile_fun("fprogram", "${F77_LINK} ${F77_LINK_SRC_F}${SRC} ${F77_LINK_TGT_F}${TGT[0].abspath()} ${F77_LINKFLAGS}", False)

@extension(".f")
def fortran_task(self, node):
    tasks = fcompile_task(self, node)
    return tasks

def fcompile_task(self, node):
    base = self.env["F77_OBJECT_FMT"] % node.name
    target = node.parent.declare(base)
    ensure_dir(target.abspath())

    task = task_factory("f77")(inputs=[node], outputs=[target])
    task.gen = self
    task.env_vars = f77_vars
    task.env = self.env
    task.func = f77_compile
    self.object_tasks.append(task)
    return [task]

class FortranBuilder(yaku.tools.Builder):
    def __init__(self, ctx):
        yaku.tools.Builder.__init__(self, ctx)

    def ccompile(self, name, sources, env=None):
        _env = copy.deepcopy(self.env)
        if env is not None:
            _env.update(env)

        task_gen = CompiledTaskGen("cccompile", self.ctx,
                                   sources, name)
        task_gen.env = _env
        apply_cpppath(task_gen)

        tasks = task_gen.process()
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
        task_gen = CompiledTaskGen("fprogram", self.ctx,
                                   sources, name)
        task_gen.env = _env

        tasks = task_gen.process()
        ltask = fprogram_task(task_gen, name)
        tasks.extend(ltask)
        for t in tasks:
            t.env = task_gen.env
        self.ctx.tasks.extend(tasks)

        outputs = []
        for t in ltask:
            outputs.extend(t.outputs)
        return outputs

    def configure(self, candidates=None):
        ctx = self.ctx
        if candidates is None:
            compiler_type = "default"
        else:
            compiler_type = candidates[0]

        if compiler_type == "default":
            fc_type = None
            for tool in ["gfortran", "g77"]:
                fc = ctx.load_tool(tool)
                if fc.detect(ctx):
                    fc_type = tool
            if fc_type is None:
                raise ValueError("No fortran compiler found")
        else:
            fc_type = compiler_type
        fc = ctx.load_tool(fc_type)
        fc.setup(ctx)
        self.configured = True

def fprogram_task(self, name):
    objects = [tsk.outputs[0] for tsk in self.object_tasks]
    def declare_target():
        folder, base = os.path.split(name)
        tmp = folder + os.path.sep + self.env["F77_PROGRAM_FMT"] % base
        return self.bld.bld_root.declare(tmp)
    target = declare_target()
    ensure_dir(target.abspath())

    task = task_factory("fprogram")(inputs=objects, outputs=[target])
    task.gen = self
    task.env = self.env
    task.func = fprogram
    task.env_vars = fprogram_vars
    return [task]

def get_builder(ctx):
    return FortranBuilder(ctx)

def mangler(name, under, double_under, case):
    return getattr(name, case)() + under + (name.replace("_", double_under) and double_under)
