import copy
import sys
import os
import types
import re

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
    node = conf.bld_root.declare(filename)
    node.write(code)
    return node

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
    builder.env = conf.env
    builder.ccompile("yomama", sources)
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
    task_gen.bld = conf
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

VALUE_SUB = re.compile('[^A-Z0-9_]')

def generate_config_h(conf_res, name):
    def value_to_string(value):
        s = value.upper()
        return VALUE_SUB.sub("_", s)

    def var_name(entry):
        if entry["type"] == "header":
            return "HAVE_%s 1" % entry["value"].upper().replace(".", "_")
        elif entry["type"] == "type":
            return "HAVE_%s 1" % entry["value"].upper().replace(" ", "_")
        elif entry["type"] == "type_size":
            return "SIZEOF_%s %s" % (
                    value_to_string(entry["value"]),
                    entry["result"])
        elif entry["type"] == "lib":
            return "HAVE_LIB%s 1" % entry["value"].upper()
        elif entry["type"] == "func":
            return "HAVE_%s 1" % entry["value"].upper()
        elif entry["type"] == "decl":
            return "HAVE_DECL_%s 1" % entry["value"].upper()
        else:
            raise ValueError("Bug: entry %s not handled" % entry)

    def comment(entry):
        if entry["type"] == "header":
            return r"""
/* Define to 1 if you have the <%s> header file. */
""" % entry["value"]
        elif entry["type"] == "lib":
            return r"""
/* Define to 1 if you have the `%s' library. */
""" % entry["value"]
        elif entry["type"] == "func":
            return r"""
/* Define to 1 if you have the `%s' function. */
""" % entry["value"]
        elif entry["type"] == "decl":
            return r"""
/* Set to 1 if %s is defined. */
""" % entry["value"]
        elif entry["type"] == "type":
            return r"""
/* Define if your compiler provides %s */
""" % entry["value"]
        elif entry["type"] == "type_size":
            return r"""
/* The size of `%s', as computed by sizeof. */
""" % entry["value"]
        else:
            raise ValueError("Bug: entry %s not handled" % entry)

    buf = StringIO()
    for entry in conf_res:
        if entry["type"] == "define":
            buf.write(entry["value"])
        else:
            var = var_name(entry)
            if entry["result"]:
                buf.write(comment(entry))
                buf.write("#define %s\n" % var)

    ensure_dir(name)
    fid = open(name, "w")
    try:
        fid.write(buf.getvalue())
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

    code = sources[0].read()
    write_log(conf.log, builder.ctx.tasks, code, "", succeed, explanation)
    return succeed
