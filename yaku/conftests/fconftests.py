"""
Fortran-specific configuration tests
"""
import sys
import copy
import os
import re
import shlex

from yaku.errors \
    import \
        TaskRunFailure
from yaku.task_manager \
    import \
        CompiledTaskGen, create_tasks
from yaku.scheduler \
    import \
        run_tasks
from yaku.utils \
    import \
        ensure_dir
from yaku.conf \
    import create_link_conf_taskgen, create_compile_conf_taskgen, \
           generate_config_h, ConfigureContext, ccompile, \
           write_log, create_file
from yaku.conftests.fconftests_imp \
    import \
        is_output_verbose, parse_flink

def create_flink_conf_taskgen(conf, name, body):
    # FIXME: make tools modules available through config context
    # FIXME: refactor commonalities between configuration taskgens
    ftool = __import__("fortran")
    code = body
    sources = [create_file(conf, code, name, ".f")]

    task_gen = CompiledTaskGen("conf", sources, name)
    task_gen.bld = conf
    task_gen.env.update(copy.deepcopy(conf.env))

    tasks = create_tasks(task_gen, sources)
    tasks.extend(ftool.fprogram_task(task_gen, name))

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

    write_log(conf.log, tasks, code, succeed, explanation)
    return succeed

def check_fcompiler(conf):
    code = """\
       program main
       end
"""

    conf.start_message("Checking whether Fortran compiler works")
    ret = create_flink_conf_taskgen(conf, "check_fc", code)
    if ret:
        conf.end_message("yes")
    else:
        conf.end_message("no !")
    return ret

def check_fortran_verbose_flag(conf):
    code = """\
       program main
       end
"""

    conf.start_message("Checking for verbose flag")
    for flag in ["-v", "--verbose", "-V"]:
        old = copy.deepcopy(conf.env["LINKFLAGS"])
        try:
            conf.env["LINKFLAGS"].append(flag)
            ret = create_flink_conf_taskgen(conf, "check_fc", code)
            if ret and is_output_verbose(conf.stdout):
                conf.end_message(flag)
                conf.env["FC_VERBOSE_FLAG"] = flag
                return True
        finally:
            conf.env["LINKFLAGS"] = old
    return False

def check_fortran_runtime_flags(conf):
    if not conf.env.has_key("FC_VERBOSE_FLAG"):
        raise ValueError("""\
You need to call check_fortran_verbose_flag before getting runtime
flags (or to define the FC_VERBOSE_FLAG variable)""")
    code = """\
       program main
       end
"""

    conf.start_message("Checking for fortran runtime flags")

    old = copy.deepcopy(conf.env["LINKFLAGS"])
    try:
        conf.env["LINKFLAGS"].append(conf.env["FC_VERBOSE_FLAG"])
        ret = create_flink_conf_taskgen(conf, "check_fc", code)
        if ret:
            flags = parse_flink(conf.stdout)
            conf.end_message(" ".join(flags))
            return True
        else:
            conf.end_message("failed !")
            return False
    finally:
        conf.env["LINKFLAGS"] = old
    return False
