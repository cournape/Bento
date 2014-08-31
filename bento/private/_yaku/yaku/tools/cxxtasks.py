import sys
import os
import copy

import yaku.tools

from yaku.task \
    import \
        task_factory
from yaku.task_manager \
    import \
        extension, CompiledTaskGen
from yaku.utils \
    import \
        find_deps, ensure_dir, get_exception
from yaku.compiled_fun \
    import \
        compile_fun
from yaku.tools.ctasks \
    import \
        apply_cpppath, apply_libdir, apply_libs, apply_define
import yaku.tools

cxxcompile, cxx_vars = compile_fun("cxx", "${CXX} ${CXXFLAGS} ${INCPATH} ${APP_DEFINES} ${CXX_TGT_F}${TGT[0].abspath()} ${CXX_SRC_F}${SRC}", False)

cxxprogram, cxxprogram_vars = compile_fun("cxxprogram", "${CXXLINK} ${CXXLINK_TGT_F}${TGT[0].abspath()} ${CXXLINK_SRC_F}${SRC} ${APP_LIBDIR} ${APP_LIBS} ${CXXLINKFLAGS}", False)

@extension('.cxx')
def cxx_hook(self, node):
    tasks = cxxcompile_task(self, node)
    self.object_tasks.extend(tasks)
    return tasks

def cxxcompile_task(self, node):
    base = self.env["CXX_OBJECT_FMT"] % node.name
    target = node.parent.declare(base)
    ensure_dir(target.abspath())

    task = task_factory("cxx")(inputs=[node], outputs=[target])
    task.gen = self
    task.env_vars = cxx_vars
    #print find_deps("foo.c", ["."])
    #task.scan = lambda : find_deps(node, ["."])
    #task.deps.extend(task.scan())
    task.env = self.env
    task.func = cxxcompile
    return [task]

def cxxprogram_task(self, name):
    objects = [tsk.outputs[0] for tsk in self.object_tasks]
    def declare_target():
        folder, base = os.path.split(name)
        tmp = folder + os.path.sep + self.env["PROGRAM_FMT"] % base
        return self.bld.path.declare(tmp)
    target = declare_target()
    ensure_dir(target.abspath())

    task = task_factory("cxxprogram")(inputs=objects, outputs=[target])
    task.gen = self
    task.env = self.env
    task.func = cxxprogram
    task.env_vars = cxxprogram_vars
    return [task]

class CXXBuilder(yaku.tools.Builder):
    def clone(self):
        return CXXBuilder(self.ctx)

    def __init__(self, ctx):
        yaku.tools.Builder.__init__(self, ctx)

    def ccompile(self, name, sources, env=None):
        task_gen = CompiledTaskGen("cxccompile", self.ctx,
                                   sources, name)
        task_gen.env = yaku.tools._merge_env(self.env, env)
        apply_define(task_gen)
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
        sources = [self.ctx.src_root.find_resource(s) for s in sources]
        task_gen = CompiledTaskGen("cxxprogram", self.ctx,
                                   sources, name)
        task_gen.env = yaku.tools._merge_env(self.env, env)
        apply_define(task_gen)
        apply_cpppath(task_gen)
        apply_libdir(task_gen)
        apply_libs(task_gen)

        tasks = task_gen.process()
        ltask = cxxprogram_task(task_gen, name)
        tasks.extend(ltask)
        for t in tasks:
            t.env = task_gen.env
        self.ctx.tasks.extend(tasks)
        self.link_task = ltask

        outputs = []
        for t in ltask:
            outputs.extend(t.outputs)
        return outputs

    def configure(self, candidates=None):
        ctx = self.ctx
        if candidates is None:
            if sys.platform == "win32":
                candidates = ["msvc", "gxx"]
            else:
                candidates = ["gxx", "cxx"]

        def _detect_cxx():
            detected = None
            sys.path.insert(0, os.path.dirname(yaku.tools.__file__))
            try:
                for cxx_type in candidates:
                    sys.stderr.write("Looking for %s (c++ compiler) ... " % cxx_type)
                    try:
                        mod = __import__(cxx_type)
                        if mod.detect(ctx):
                            sys.stderr.write("yes\n")
                            detected = cxx_type
                            break
                    except ImportError:
                        raise
                    except:
                        pass
                    sys.stderr.write("no!\n")
                return detected
            finally:
                sys.path.pop(0)

        cxx_type = _detect_cxx()
        if cxx_type is None:
            raise ValueError("No CXX compiler found!")
        cxx = ctx.load_tool(cxx_type)
        cxx.setup(ctx)

        if sys.platform != "win32":
            ar = ctx.load_tool("ar")
            ar.setup(ctx)
        self.configured = True

def get_builder(ctx):
    return CXXBuilder(ctx)
