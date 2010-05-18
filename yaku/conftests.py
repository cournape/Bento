import copy
import os

from utils \
    import \
        ensure_dir
from conf \
    import create_link_conf_taskgen, create_compile_conf_taskgen, \
           generate_config_h, ConfigureContext

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
