import os
import sys
import shutil
import subprocess

from cStringIO \
    import \
        StringIO

import lib2to3.main

from yaku.errors \
    import \
        TaskRunFailure
from yaku.task \
    import \
        task_factory
from yaku.task_manager \
    import \
        TaskGen, extension
from yaku.pprint \
    import \
        pprint

import yaku.tools

def convert_func(self):
    if not len(self.inputs) == 1:
        raise ValueError("convert_func needs exactly one input")
    source, target = self.inputs[0], self.outputs[0]

    pprint('GREEN', "%-16s%s" % (self.name.upper(),
           " ".join([s.srcpath() for s in self.inputs])))
    cmd = ["2to3", "-w", "--no-diffs", "-n", source.abspath()]
    st = subprocess.call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if st != 0:
        pprint('RED', "FAILED %-16s%s" % (self.name.upper(),
               " ".join([s.srcpath() for s in self.inputs])))
        raise TaskRunFailure(cmd)
    target.write(source.read())

def copy_func(self):
    source, target = self.inputs[0], self.outputs[0]
    pprint('YELLOW', "%-16s%s" % (self.name.upper(),
           " ".join([s.srcpath() for s in self.inputs])))
    target.write(source.read())

class Py3kConverterBuilder(yaku.tools.Builder):
    def __init__(self, ctx):
        super(Py3kConverterBuilder, self).__init__(ctx)

    def _process_exclude(self, env):
        if "2TO3_EXCLUDE_LIST" in env:
            excludes = env["2TO3_EXCLUDE_LIST"]
        else:
            excludes = []
        dirs = []
        fs = []
        for e in excludes:
            n = self.ctx.src_root.find_node(e)
            if os.path.isdir(n.abspath()):
                dirs.append(n)
            else:
                fs.append(n)

        def _exclude(n):
            for d in dirs:
                if n.is_child_of(d):
                    return True
            if n in fs:
                return True
            return False
        return _exclude

    def convert(self, name, sources, env=None):
        # Basic principle: we first copy the whole tree (defined by the sources
        # list) into a temporary directory, which is then used for the
        # convertion. Notes:
        # - the whole tree needs to be copied before any 2to3 execution as 2to3
        # depends on the tree structure (e.g. for local vs absolute imports)
        # - because 2to3 can only modify files in place, we need to copy things
        # twice to avoid re-applying 2to3 several times (2to3 is not
        # idem-potent).
        # - the exclude process is particularly ugly...
        env = yaku.tools._merge_env(self.env, env)

        flter = self._process_exclude(env)
        self.env["__2TO3_FILTER"] = flter

        files = [self.ctx.src_root.find_resource(f) for f in sources]

        convert_tf = task_factory("2to3")
        copy_tf = task_factory("2to3_prepare")
        convert_tf.before.append(copy_tf.__name__)

        py3k_tmp = self.ctx.bld_root.declare("_py3k_tmp")
        py3k_top = self.ctx.bld_root.declare("py3k")
        tasks = []
        for f in files:
            target = py3k_tmp.declare(f.srcpath())
            task = copy_tf(inputs=[f], outputs=[target])
            task.func = copy_func
            task.env_vars = {}
            task.env = env
            tasks.append(task)

            if f.name.endswith(".py") and not flter(f):
                source = target
                target = py3k_top.declare(source.path_from(py3k_tmp))
                task = convert_tf(inputs=[source], outputs=[target])
                task.func = convert_func
                task.env_vars = {}
                task.env = env
                tasks.append(task)
            else:
                source = f
                target = py3k_top.declare(source.srcpath())
                task = copy_tf(inputs=[source], outputs=[target])
                task.func = copy_func
                task.env_vars = {}
                task.env = env
                tasks.append(task)

        self.ctx.tasks.extend(tasks)

        outputs = []
        for t in tasks:
            outputs.extend(t.outputs)
        return outputs

def get_builder(ctx):
    return Py3kConverterBuilder(ctx)
