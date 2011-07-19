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
        ensure_dir, get_exception
from yaku.tools.ctasks \
    import \
        apply_libdir
from yaku.errors \
    import \
        TaskRunFailure
from yaku.scheduler \
    import \
        run_tasks
from yaku.conf \
    import \
        with_conf_blddir, create_file, write_log
import yaku.tools

f77_compile, f77_vars = compile_fun("f77", "${F77} ${F77FLAGS} ${F77_TGT_F}${TGT[0].abspath()} ${F77_SRC_F}${SRC}", False)

fprogram, fprogram_vars = compile_fun("fprogram", "${F77_LINK} ${F77_LINK_SRC_F}${SRC} ${F77_LINK_TGT_F}${TGT[0].abspath()} ${APP_LIBDIR} ${F77_LINKFLAGS}", False)

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

    def _try_task_maker(self, task_maker, name, body):
        conf = self.ctx
        code =  body
        sources = [create_file(conf, code, name, ".f")]

        task_gen = CompiledTaskGen("conf", conf, sources, name)
        task_gen.env.update(copy.deepcopy(conf.env))

        tasks = task_maker(task_gen, name)
        self.ctx.last_task = tasks[-1]

        for t in tasks:
            t.disable_output = True
            t.log = conf.log

        succeed = False
        explanation = None
        try:
            run_tasks(conf, tasks)
            succeed = True
        except TaskRunFailure:
            e = get_exception()
            explanation = str(e)

        write_log(conf, conf.log, tasks, code, succeed, explanation)
        return succeed

    def try_compile(self, name, body):
        # FIXME: temporary workaround for cyclic import between ctasks and conf
        #from yaku.conf import with_conf_blddir
        return with_conf_blddir(self.ctx, name, body,
                                lambda : self._try_task_maker(self._compile, name, body))

    def compile(self, name, sources, env=None):
        _env = copy.deepcopy(self.env)
        if env is not None:
            _env.update(env)

        task_gen = CompiledTaskGen("fcompile", self.ctx,
                                   sources, name)
        task_gen.env = _env
        tasks = self._compile(name, sources)
        self.ctx.tasks.extend(tasks)

        outputs = []
        for t in tasks:
            outputs.extend(t.outputs)
        return outputs

    def _compile(self, task_gen, name):
        tasks = task_gen.process()
        for t in tasks:
            t.env = task_gen.env
        return tasks

    def try_static_library(self, name, body):
        # FIXME: temporary workaround for cyclic import between ctasks and conf
        #from yaku.conf import with_conf_blddir
        cc_builder = self.ctx.builders["ctasks"]
        return with_conf_blddir(self.ctx, name, body,
                                lambda : self._try_task_maker(cc_builder._static_library, name, body))

    def try_program(self, name, body):
        # FIXME: temporary workaround for cyclic import between ctasks and conf
        #from yaku.conf import with_conf_blddir
        return with_conf_blddir(self.ctx, name, body,
                                lambda : self._try_task_maker(self._program, name, body))

    def program(self, name, sources, env=None):
        _env = copy.deepcopy(self.env)
        if env is not None:
            _env.update(env)

        sources = [self.ctx.src_root.find_resource(s) for s in sources]
        task_gen = CompiledTaskGen("fprogram", self.ctx,
                                   sources, name)
        task_gen.env = _env
        tasks = self._program(task_gen, name)

        self.ctx.tasks.extend(tasks)

        outputs = []
        for t in task_gen.link_task:
            outputs.extend(t.outputs)
        return outputs

    def _program(self, task_gen, name):
        apply_libdir(task_gen)

        tasks = task_gen.process()
        ltask = fprogram_task(task_gen, name)
        tasks.extend(ltask)
        for t in tasks:
            t.env = task_gen.env
        task_gen.link_task = ltask
        return tasks

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
        return self.bld.path.declare(tmp)
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
