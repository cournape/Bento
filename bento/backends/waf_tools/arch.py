import re

from waflib.Tools.c_config import SNIP_EMPTY_PROGRAM
from waflib.Configure import conf

ARCHS = ["i386", "x86_64", "ppc", "ppc64"]

FILE_MACHO_RE = re.compile("Mach-O.*object ([a-zA-Z_0-9]+)")

@conf
def check_cc_arch(conf):
    env = conf.env
    archs = []

    for arch in ARCHS:
        env.stash()
        try:
            env.append_value('CFLAGS', ['-arch', arch])
            env.append_value('LINKFLAGS', ['-arch', arch])
            try:
                conf.check_cc(fragment=SNIP_EMPTY_PROGRAM, msg="Checking for %r suport" % arch)
                archs.append(arch)
            except conf.errors.ConfigurationError:
                pass
        finally:
            env.revert()

    env["ARCH_CC"] = archs

#def detect_arch(filename):

@conf
def check_cc_default_arch(conf):
    start_msg = "Checking for default CC arch"
    fragment = SNIP_EMPTY_PROGRAM
    output_var = "DEFAULT_CC_ARCH"

    return _check_default_arch(conf, start_msg, fragment, output_var)

@conf
def check_cxx_default_arch(conf):
    start_msg = "Checking for default CXX arch"
    fragment = SNIP_EMPTY_PROGRAM
    output_var = "DEFAULT_CXX_ARCH"

    return _check_default_arch(conf, start_msg, fragment, output_var)

@conf
def check_fc_default_arch(conf):
    start_msg = "Checking for default FC arch"
    fragment = """\
      program main
      end
"""
    output_var = "DEFAULT_FC_ARCH"
    compile_filename = 'test.f'
    features = "fc fcprogram"

    return _check_default_arch(conf, start_msg, fragment, output_var, compile_filename, features)

@conf
def _check_default_arch(conf, start_msg, fragment, output_var, compile_filename="test.c", features="c cprogram"):
    env = conf.env

    if not "FILE_BIN" in conf.env:
        file_bin = conf.find_program(["file"], var="FILE_BIN")
    else:
        file_bin = conf.env.FILE_BIN

    conf.start_msg(start_msg)
    ret = conf.check_cc(fragment=fragment, compile_filename=compile_filename, features=features)
    task_gen = conf.test_bld.groups[0][0]
    obj_filename = task_gen.tasks[0].outputs[0].abspath()
    out = conf.cmd_and_log([file_bin, obj_filename])
    m = FILE_MACHO_RE.search(out)
    if m is None:
        conf.fatal("Could not determine arch from output %r" % out)
    else:
        default_arch = m.group(1)
        conf.env[output_var] = default_arch
        conf.end_msg(default_arch)
