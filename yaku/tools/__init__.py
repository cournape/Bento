import os
import sys
import copy

from yaku._config \
    import \
        TOOLDIRS
from yaku.task_manager \
    import \
        CompiledTaskGen, TaskGen
from yaku.errors \
    import \
        TaskRunFailure
from yaku.scheduler \
    import \
        run_tasks
from yaku.conf \
    import \
        with_conf_blddir, create_file, write_log

def import_tools(tool_list, tooldirs=None):
    old_sys = sys.path[:]
    if tooldirs is not None:
        sys.path = tooldirs + TOOLDIRS + sys.path
    else:
        sys.path = TOOLDIRS + sys.path

    try:
        ret = {}
        for t in tool_list:
            ret[t] = __import__(t)
        return ret
    finally:
        sys.path = old_sys

class Builder(object):
    def __init__(self, ctx):
        self.configured = False
        self.ctx = ctx
        self.env = copy.deepcopy(ctx.env)

    def to_nodes(self, filenames):
        # Convert source filenames to nodes
        return [self.ctx.src_root.find_resource(s) for s in filenames]

    def configure(self):
        pass

    def _task_gen_factory(self, name, target, sources, env):
        sources = self.to_nodes(sources)

        task_gen = TaskGen(name, self.ctx, sources, target)
        task_gen.env = _merge_env(self.env, env)
        tasks = task_gen.process()
        for t in tasks:
            t.env = task_gen.env
        self.ctx.tasks.extend(tasks)

        outputs = tasks[0].outputs[:]
        return outputs

def try_task_maker(conf, task_maker, name, body, headers, env=None):
    if headers:
        head = "\n".join(["#include <%s>" % h for h in headers])
    else:
        head = ""
    code = "\n".join([c for c in [head, body]])
    sources = [create_file(conf, code, name, ".c")]

    task_gen = CompiledTaskGen("conf", conf, sources, name)
    task_gen.env.update(copy.deepcopy(conf.env))
    task_gen.env = _merge_env(task_gen.env, env)
    task_gen.env.prepend("LIBDIR", os.curdir)

    tasks = task_maker(task_gen, name)
    conf.last_task = tasks[-1]

    for t in tasks:
        t.disable_output = True
        t.log = conf.log

    succeed = False
    explanation = None
    try:
        run_tasks(conf, tasks)
        succeed = True
    except TaskRunFailure, e:
        explanation = str(e)

    write_log(conf, conf.log, tasks, code, succeed, explanation)
    return succeed

def _merge_env(_env, new_env):
    if new_env is not None:
        ret = copy.copy(_env)
        for k, v in new_env.items():
            if hasattr(_env[k], "extend"):
                old = copy.copy(_env[k])
                old.extend(v)
                ret[k] = old
            else:
                ret[k] = v
        return ret
    else:
        return _env

