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
           write_log, create_file, create_conf_blddir
from yaku.conftests.fconftests_imp \
    import \
        is_output_verbose, parse_flink

FC_VERBOSE_FLAG = "FC_VERBOSE_FLAG"
FC_RUNTIME_LDFLAGS = "FC_RUNTIME_LDFLAGS"
FC_DUMMY_MAIN = "FC_DUMMY_MAIN"

def create_fprogram_conf_taskgen(conf, name, body):
    # FIXME: make tools modules available through config context
    ftool = __import__("fortran")
    builder = ftool.fprogram_task

    old_root, new_root = create_conf_blddir(conf, name, body)
    try:
        conf.bld_root = new_root
        return _create_fbinary_conf_taskgen(conf, name, body, builder)
    finally:
        conf.bld_root = old_root

def create_fstatic_conf_taskgen(conf, name, body):
    # FIXME: make tools modules available through config context
    ctool = __import__("ctasks")
    builder = ctool.static_link_task

    old_root, new_root = create_conf_blddir(conf, name, body, builder)
    try:
        conf.bld_root = new_root
        return _create_fbinary_conf_taskgen(conf, name, body, builder)
    finally:
        conf.bld_root = old_root

def _create_fbinary_conf_taskgen(conf, name, body, builder):
    # FIXME: refactor commonalities between configuration taskgens
    code = body
    sources = [create_file(conf, code, name, ".f")]

    task_gen = CompiledTaskGen("conf", sources, name)
    task_gen.bld = conf
    task_gen.env.update(copy.deepcopy(conf.env))

    tasks = create_tasks(task_gen, sources)
    tasks.extend(builder(task_gen, name))

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
                conf.env[FC_VERBOSE_FLAG] = flag
                return True
        finally:
            conf.env["LINKFLAGS"] = old
    return False

def check_fortran_runtime_flags(conf):
    if not conf.env.has_key(FC_VERBOSE_FLAG):
        raise ValueError("""\
You need to call check_fortran_verbose_flag before getting runtime
flags (or to define the %s variable)""" % FC_VERBOSE_FLAG)
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
            conf.env[FC_RUNTIME_LDFLAGS] = flags
            return True
        else:
            conf.end_message("failed !")
            return False
    finally:
        conf.env["LINKFLAGS"] = old
    return False

def check_fortran_dummy_main(conf):
    code_tpl = """\
#ifdef __cplusplus
        extern "C"
#endif
int %(main)s()
{
    return 1;
}

int main()
{
    return 0;
}
"""

    conf.start_message("Checking whether fortran needs dummy main")

    old = copy.deepcopy(conf.env["LINKFLAGS"])
    try:
        conf.env["LINKFLAGS"].extend(conf.env[FC_RUNTIME_LDFLAGS])
        ret = create_link_conf_taskgen(conf, "check_fc_dummy_main",
                code_tpl % {"main": "FC_DUMMY_MAIN"})
        if ret:
            conf.end_message("none")
            conf.env[FC_DUMMY_MAIN] = None
            return True
        else:
            conf.end_message("failed !")
            return False
    finally:
        conf.env["LINKFLAGS"] = old

def check_fortran_mangling(conf):
    subr = """
      subroutine foobar()
      return
      end
      subroutine foo_bar()
      return
      end
"""
    main_tmpl = """
      int %s() { return 1; }
"""
    prog_tmpl = """
      void %(foobar)s(void);
      void %(foo_bar)s(void);
      int main() {
      %(foobar)s();
      %(foo_bar)s();
      return 0;
      }
"""

    conf.start_message("Checking fortran mangling scheme")
    old = {}
    for k in ["LINKFLAGS", "LIBS", "LIBDIR"]:
        old[k] = copy.deepcopy(conf.env[k])
    try:
        mangling_lib = "check_fc_mangling_lib"
        ret = create_fstatic_conf_taskgen(conf, mangling_lib, subr)
        if ret:
            if conf.env[FC_DUMMY_MAIN] is not None:
                main = main_tmpl % conf.env["FC_DUMMY_MAIN"]
            else:
                main = ""
            conf.env["LIBS"].insert(0, mangling_lib)
            libdir = conf.last_task.outputs[-1].parent.abspath()
            conf.env["LIBDIR"].insert(0, libdir)

            for u, du, case in mangling_generator():
                names = {"foobar": mangle_func("foobar", u, du, case),
                         "foo_bar": mangle_func("foo_bar", u, du, case)}
                prog = prog_tmpl % names
                ret = create_link_conf_taskgen(conf,
                        "check_fc_mangling_main", main + prog)
                if ret:
                    conf.env["FC_MANGLING"] = (u, du, case)
                    conf.end_message("%r %r %r" % (u, du, case))
                    return
            conf.end_message("failed !")
        else:
            conf.end_message("failed !")

    finally:
        for k in old:
            conf.env[k] = old[k]

def mangling_generator():
    for under in ['_', '']:
        for double_under in ['', '_']:
            for case in ["lower", "upper"]:
                yield under, double_under, case

def mangle_func(name, under, double_under, case):
    return getattr(name, case)() + under + (name.find("_") != -1 and double_under or '')
