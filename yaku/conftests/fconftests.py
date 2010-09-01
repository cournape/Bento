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
           write_log2, create_file

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

    write_log2(conf.log, tasks, code, succeed, explanation)
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

GCC_DRIVER_LINE = re.compile('^Driving:')
POSIX_STATIC_EXT = re.compile('\S+\.a')
POSIX_LIB_FLAGS = re.compile('-l\S+')

def is_output_verbose(out):
    for line in out.splitlines():
        if not GCC_DRIVER_LINE.search(line):
            if POSIX_STATIC_EXT.search(line) or POSIX_LIB_FLAGS.search(line):
                return True
    return False

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
            print parse_flink(conf.stdout)
            return False
        else:
            conf.end_message("failed !")
            return False
    finally:
        conf.env["LINKFLAGS"] = old
    return False

# linkflags which match those are ignored
LINKFLAGS_IGNORED = [r'-lang*', r'-lcrt[a-zA-Z0-9]*\.o', r'-lc$', r'-lSystem',
                     r'-libmil', r'-LIST:*', r'-LNO:*']
if os.name == 'nt':
    LINKFLAGS_IGNORED.extend([r'-lfrt*', r'-luser32',
            r'-lkernel32', r'-ladvapi32', r'-lmsvcrt',
            r'-lshell32', r'-lmingw', r'-lmoldname'])
else:
    LINKFLAGS_IGNORED.append(r'-lgcc*')

RLINKFLAGS_IGNORED = [re.compile(f) for f in LINKFLAGS_IGNORED]

def _match_ignore(line):
    """True if the line should be ignored."""
    if [i for i in RLINKFLAGS_IGNORED if i.match(line)]:
        return True
    else:
        return False

def parse_flink(output):
    """Given the output of verbose link of fortran compiler, this
    returns a list of flags necessary for linking using the standard
    linker."""
    # TODO: On windows ?
    final_flags = []
    for line in output.splitlines():
        if not GCC_DRIVER_LINE.match(line):
            _parse_f77link_line(line, final_flags)
    return final_flags

SPACE_OPTS = re.compile('^-[LRuYz]$')
NOSPACE_OPTS = re.compile('^-[RL]')

def _parse_f77link_line(line, final_flags):
    lexer = shlex.shlex(line, posix = True)
    lexer.whitespace_split = True

    t = lexer.get_token()
    tmp_flags = []
    while t:
        def parse(token):
            # Here we go (convention for wildcard is shell, not regex !)
            #   1 TODO: we first get some root .a libraries
            #   2 TODO: take everything starting by -bI:*
            #   3 Ignore the following flags: -lang* | -lcrt*.o | -lc |
            #   -lgcc* | -lSystem | -libmil | -LANG:=* | -LIST:* | -LNO:*)
            #   4 take into account -lkernel32
            #   5 For options of the kind -[[LRuYz]], as they take one argument
            #   after, the actual option is the next token 
            #   6 For -YP,*: take and replace by -Larg where arg is the old
            #   argument
            #   7 For -[lLR]*: take

            # step 3
            if _match_ignore(token):
                pass
            # step 4
            elif token.startswith('-lkernel32') and sys.platform == 'cygwin':
                tmp_flags.append(token)
            # step 5
            elif SPACE_OPTS.match(token):
                t = lexer.get_token()
                if t.startswith('P,'):
                    t = t[2:]
                for opt in t.split(os.pathsep):
                    tmp_flags.append('-L%s' % opt)
            # step 6
            elif NOSPACE_OPTS.match(token):
                tmp_flags.append(token)
            # step 7
            elif POSIX_LIB_FLAGS.match(token):
                tmp_flags.append(token)
            else:
                # ignore anything not explicitely taken into account
                pass

            t = lexer.get_token()
            return t
        t = parse(t)

    final_flags.extend(tmp_flags)
    return final_flags
