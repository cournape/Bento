import copy
import sys
import os
import types

from hashlib \
    import \
        md5
from os.path \
    import \
        join
from cPickle \
    import \
        load, dump
from cStringIO \
    import \
        StringIO

from errors \
    import \
        TaskRunFailure
from task_manager \
    import \
        CompiledTaskGen, create_tasks, run_tasks
from compiled_fun \
    import \
        compile_fun
from utils \
    import \
        ensure_dir

from ctasks \
    import \
        link_task, apply_libs, apply_libdir

CONF_CACHE_FILE = ".conf.cpk"

class ConfigureContext(object):
    def __init__(self):
        self.cache = {}
        self.env = {}
        self.conf_results = []

def apply_cpppath(task_gen):
    cpppaths = task_gen.env["CPPPATH"]
    implicit_paths = set([
        os.path.join(task_gen.env["BLDDIR"], os.path.dirname(s))
        for s in task_gen.sources])
    cpppaths = list(implicit_paths) + cpppaths
    task_gen.env["INCPATH"] = [
            task_gen.env["INCPATH_FMT"] % p
            for p in cpppaths]

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

    task_gen = CompiledTaskGen("conf", sources, name)
    task_gen.env.update(copy.deepcopy(conf.env))
    task_gen.env["INCPATH"] = ""

    tasks = create_tasks(task_gen, sources)
    for t in tasks:
        t.disable_output = True
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

def write_log(log, tasks, code, msg, succeed, explanation):
    conf.log.write("------------------------------------\n")
    conf.log.write(msg + "\n")
    conf.log.write("Tested code is:\n")
    conf.log.write("~~~~~~~~~\n")
    conf.log.write(code)
    conf.log.write("~~~~~~~~~\n")

    if succeed:
        conf.log.write("---> Succeeded !\n")
    else:
        conf.log.write("---> Failed: %s !\n" % explanation)

    s = StringIO()
    s.write("Command sequence was:\n")
    log_command(s, tasks)
    conf.log.write(s.getvalue())
    conf.log.write("\n")

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
    tasks.extend(link_task(task_gen, name))

    for t in tasks:
        t.disable_output = True
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

def check_compiler(conf):
    code = """\
int main(void)
{
    return 0;
}
"""

    ret = create_link_conf_taskgen(conf, "check_cc", code,
                        None, "Checking whether C compiler works")
    return ret

def check_type(conf, type_name, headers=None):
    code = r"""
int main() {
  if ((%(name)s *) 0)
    return 0;
  if (sizeof (%(name)s))
    return 0;
}
""" % {'name': type_name}

    ret = create_compile_conf_taskgen(conf, "check_type", code,
                        headers, "Checking for type %s" % type_name)
    conf.conf_results.append({"type": "type", "value": type_name,
                              "result": ret})
    return ret

def check_header(conf, header):
    code = r"""
#include <%s>
""" % header

    ret = create_compile_conf_taskgen(conf, "check_header", code,
                        None, "Checking for header %s" % header)
    conf.conf_results.append({"type": "header", "value": header,
                              "result": ret})
    return ret

def check_lib(conf, lib):
    code = r"""
int main()
{
    return 0;
}
"""

    old_lib = copy.deepcopy(conf.env["LIBS"])
    try:
        conf.env["LIBS"].insert(0, lib)
        ret = create_link_conf_taskgen(conf, "check_lib", code,
                            None, "Checking for library %s" % lib)
    finally:
        conf.env["LIBS"] = old_lib
    conf.conf_results.append({"type": "lib", "value": lib,
                              "result": ret})
    return ret

def check_func(conf, func, libs=None):
    if libs is None:
        libs = []
    # Handle MSVC intrinsics: force MS compiler to make a function
    # call. Useful to test for some functions when built with
    # optimization on, to avoid build error because the intrinsic and
    # our 'fake' test declaration do not match.
    code = r"""
char %(func)s (void);

#ifdef _MSC_VER
#pragma function(%(func)s)
#endif

int main (void)
{
    return %(func)s();
}
""" % {"func": func}

    old_lib = copy.deepcopy(conf.env["LIBS"])
    try:
        for lib in libs[::-1]:
            conf.env["LIBS"].insert(0, lib)
        ret = create_link_conf_taskgen(conf, "check_func", code,
                            None, "Checking for function %s" % func)
    finally:
        conf.env["LIBS"] = old_lib
    conf.conf_results.append({"type": "func", "value": func,
                              "result": ret})
    return ret

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
            var = var_name(entry)
            if entry["result"]:
                fid.write("#define %s 1\n\n" % var)
            else:
                fid.write("/*#under %s*/\n\n" % var)
    finally:
        fid.close()

if __name__ == "__main__":
    # TODO
    #  - support for env update
    #  - config header support
    #  - confdefs header support
    conf = ConfigureContext()
    if os.path.exists(CONF_CACHE_FILE):
        with open(CONF_CACHE_FILE) as fid:
            conf.cache = load(fid)

    conf.env.update({"CC": ["gcc"],
        "CFLAGS": ["-Wall"],
        "SHLINK": ["gcc"],
        "SHLINKFLAGS": [],
        "LIBS": [],
        "LIBS_FMT": "-l%s",
        "LIBDIR": [],
        "LIBDIR_FMT": "-L%s",
        "BLDDIR": "build/conf",
        "VERBOSE": False})
    log_filename = os.path.join("build", "config.log")
    ensure_dir(log_filename)
    conf.log = open(log_filename, "w")

    check_compiler(conf)
    check_header(conf, "stdio.h")
    check_header(conf, "stdio")
    check_type(conf, "char")
    #check_type(conf, "complex")
    check_type(conf, "complex", headers=["complex.h"])
    check_lib(conf, lib="m")
    #check_lib(conf, lib="mm")
    check_func(conf, "floor", libs=["m"])
    check_func(conf, "floor")

    generate_config_h(conf.conf_results, "build/conf/config.h")

    conf.log.close()
    with open(CONF_CACHE_FILE, "w") as fid:
        dump(conf.cache, fid)
