import copy
import sys
import os
import types

try:
    from hashlib import md5
except ImportError:
    from md5 import md5

from os.path \
    import \
        join
from cStringIO \
    import \
        StringIO

from yaku.errors \
    import \
        TaskRunFailure
from yaku.task_manager \
    import \
        CompiledTaskGen, create_tasks
from yaku.scheduler \
    import \
        run_tasks
from yaku.compiled_fun \
    import \
        compile_fun
from yaku.utils \
    import \
        ensure_dir

from yaku.tools.ctasks \
    import \
        shlink_task, apply_libs, apply_libdir, ccprogram_task

class ConfigureContext(object):
    def __init__(self):
        self.cache = {}
        self.env = {}
        self.conf_results = []

def create_file(conf, code, prefix="", suffix=""):
    filename = "%s%s%s" % (prefix, md5(code).hexdigest(), suffix)
    filename = join(conf.env["BLDDIR"], filename)
    ensure_dir(filename)
    open(filename, "w").write(code)
    return filename

def create_compile_conf_taskgen(conf, name, body, headers,
        msg, extension=".c"):
    if headers:
        head = "\n".join(["#include <%s>" % h for h in headers])
    else:
        head = ""
    code = "\n".join([c for c in [head, body]])
    sources = [create_file(conf, code, name, extension)]

    conf.tasks = [] # XXX: hack
    builder = conf.builders["ctasks"]
    builder.ccompile("yomama", sources, conf.env)
    # XXX: accessing tasks like this is ugly - the whole logging thing
    # needs more thinking
    for t in builder.ctx.tasks:
        t.disable_output = True
        t.log = conf.log
    sys.stderr.write(msg + "... ")

    succeed = False
    explanation = None
    try:
        run_tasks(conf, builder.ctx.tasks)
        succeed = True
        sys.stderr.write("yes\n")
    except TaskRunFailure, e:
        sys.stderr.write("no\n")
        explanation = str(e)

    write_log(conf.log, builder.ctx.tasks, code, msg, succeed, explanation)
    return succeed

def write_log(log, tasks, code, msg, succeed, explanation):
    log.write("------------------------------------\n")
    log.write(msg + "\n")
    log.write("Tested code is:\n")
    log.write("~~~~~~~~~\n")
    log.write(code)
    log.write("~~~~~~~~~\n")

    if succeed:
        log.write("---> Succeeded !\n")
    else:
        log.write("---> Failed: %s !\n" % explanation)

    s = StringIO()
    s.write("Command sequence was:\n")
    log_command(s, tasks)
    log.write(s.getvalue())
    log.write("\n")

def log_command(logger, tasks):
    # XXX: hack to retrieve the command line and put it in the
    # output...
    for t in tasks:
        def fake_exec(self, cmd, cwd):
            logger.write(" ".join(cmd))
            logger.write("\n")
        t.exec_command = types.MethodType(fake_exec, t,
                t.__class__)
        t.run()

def create_link_conf_taskgen(conf, name, body, headers,
        msg, extension=".c"):
    if headers:
        head = "\n".join(["#include <%s>" % h for h in headers])
    else:
        head = ""
    code = "\n".join([c for c in [head, body]])
    sources = [create_file(conf, code, name, extension)]

    task_gen = CompiledTaskGen("conf", sources, name)
    task_gen.env.update(copy.deepcopy(conf.env))
    task_gen.env["INCPATH"] = ""
    apply_libs(task_gen)
    apply_libdir(task_gen)

    tasks = create_tasks(task_gen, sources)
    tasks.extend(ccprogram_task(task_gen, name))

    for t in tasks:
        t.disable_output = True
        t.log = conf.log
    sys.stderr.write(msg + "... ")

    succeed = False
    explanation = None
    try:
        run_tasks(conf, tasks)
        succeed = True
        sys.stderr.write("yes\n")
    except TaskRunFailure, e:
        sys.stderr.write("no\n")
        explanation = str(e)

    write_log(conf.log, tasks, code, msg, succeed, explanation)
    return succeed

def generate_config_h(conf_res, name):
    def var_name(entry):
        if entry["type"] == "header":
            return "HAVE_%s" % entry["value"].upper().replace(".", "_")
        elif entry["type"] == "type":
            return "HAVE_%s" % entry["value"].upper().replace(" ", "_")
        elif entry["type"] == "lib":
            return "HAVE_LIB%s" % entry["value"].upper()
        elif entry["type"] == "func":
            return "HAVE_FUNC_%s" % entry["value"].upper()

    ensure_dir(name)
    fid = open(name, "w")
    try:
        for entry in conf_res:
            if entry["type"] == "define":
                fid.write(entry["value"])
            else:
                var = var_name(entry)
                if entry["result"]:
                    fid.write("#define %s 1\n\n" % var)
                else:
                    fid.write("/*#undef %s*/\n\n" % var)
    finally:
        fid.close()

def ccompile(conf, sources):
    conf.tasks = [] # XXX: hack
    builder = conf.builders["ctasks"]
    builder.ccompile("yomama", sources, conf.env)
    # XXX: accessing tasks like this is ugly - the whole logging thing
    # needs more thinking
    for t in builder.ctx.tasks:
        t.disable_output = True
        t.log = conf.log

    succeed = False
    explanation = None
    try:
        run_tasks(conf, builder.ctx.tasks)
        succeed = True
    except TaskRunFailure, e:
        explanation = str(e)

    f = open(sources[0])
    try:
        code = f.read()
        write_log(conf.log, builder.ctx.tasks, code, "", succeed, explanation)
    finally:
        f.close()
    return succeed
