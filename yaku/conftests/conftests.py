import sys
import copy
import os

from yaku.utils \
    import \
        ensure_dir
from yaku.conf \
    import create_link_conf_taskgen, create_compile_conf_taskgen, \
           generate_config_h, ConfigureContext, ccompile, create_file

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

def check_type_size(conf, type_name, headers=None, expect=None):
    """\
    This check can be used to get the size of a given type, or to
    check whether the type is of expected size.

    Arguments
    ---------
    conf : object
        configure context instance
    type_name : str
        the type to check
    includes : sequence
        list of headers to include in the test code before testing the
        type
    expect : sequence
        if given, will test wether the type has the given number of
            bytes.  If not given, will automatically find the size.
    """

    # First check the type can be compiled
    if headers:
        headers_code = "\n".join(["#include <%s>\n" % h \
                                  for h in headers])
    else:
        headers_code = ""

    sys.stderr.write("Checking for sizeof %s ..." % type_name)
    body = r"""
%(headers)s
typedef %(type)s yaku_check_sizeof_type;
int main ()
{
    static int test_array [1 - 2 * !(((long) (sizeof (yaku_check_sizeof_type))) >= 0)];
    test_array [0] = 0

    ;
    return 0;
}
""" % {"type": type_name, "headers": headers_code}

    if not ccompile(conf, [create_file(conf, body, "yomama", ".c")]):
        sys.stderr.write("Failed !\n")
        return False

    if expect is None:
        # this fails to *compile* if size > sizeof(type)
        body = r"""
%(headers)s
typedef %(type)s npy_check_sizeof_type;
int main ()
{
    static int test_array [1 - 2 * !(((long) (sizeof (npy_check_sizeof_type))) <= %(size)s)];
    test_array [0] = 0

    ;
    return 0;
}
"""
        # The principle is simple: we first find low and high bounds
        # of size for the type, where low/high are looked up on a log
        # scale. Then, we do a binary search to find the exact size
        # between low and high
        low = 0
        mid = 0
        while True:
            if ccompile(conf, [create_file(conf, body % {'type': type_name, 'size': mid, "headers": headers_code}, suffix=".c")]):
                break
            #log.info("failure to test for bound %d" % mid)
            low = mid + 1
            mid = 2 * mid + 1

        high = mid
        # Binary search:
        while low != high:
            mid = (high - low) / 2 + low
            if ccompile(conf, [create_file(conf, body % {'type': type_name, 'size': mid, "headers": headers_code}, suffix=".c")]):
                high = mid
            else:
                low = mid + 1
        sys.stderr.write(" %d\n" % low)
        return low
    else:
        raise NotImplementedError("Expect arg not yet implemented")

def define(conf, name, value=None, comment=None):
    """\
    Define a new preprocessing symbol in the current config header.

    If value is None. then #define name is written. If value is not
    none, then #define name value is written.

    Parameters
    ----------
    conf: object
        Instance of the current configure context
    name: str
        Name of the symbol to define
    value : (None)
        If given and not None, the symbol will have this value
    comment: str
        will be put as a C comment in the header, to explain the
        meaning of the value (appropriate C comments /* and */ will be
        put automatically).
    """
    lines = []
    if comment:
        comment_str = "/* %s */" % comment
        lines.append(comment_str)

    if value is not None:
        define_str = "#define %s %s" % (name, value)
    else:
        define_str = "#define %s" % name
    lines.append(define_str)
    lines.append('')
    content = "\n".join(lines)

    conf.conf_results.append({"type": "define", "value": content,
        "result": True})

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

def check_funcs_at_once(conf, funcs, libs=None):
    if libs is None:
        libs = []

    header = []
    header = ['#ifdef __cplusplus']
    header.append('extern "C" {')
    header.append('#endif')
    for f in funcs:
        header.append("\tchar %s();" % f)
        # Handle MSVC intrinsics: force MS compiler to make a function
        # call. Useful to test for some functions when built with
        # optimization on, to avoid build error because the intrinsic
        # and our 'fake' test declaration do not match.
        header.append("#ifdef _MSC_VER")
        header.append("#pragma function(%s)" % f)
        header.append("#endif")
    header.append('#ifdef __cplusplus')
    header.append('};')
    header.append('#endif')
    header = "\n".join(header)

    tmp = []
    for f in funcs:
        tmp.append("\t%s();" % f)
    tmp = "\n".join(tmp)

    body = r"""
%(include)s
%(header)s

int main (void)
{
    %(tmp)s
        return 0;
}
""" % {"tmp": tmp, "include": "", "header": header}

    old_lib = copy.deepcopy(conf.env["LIBS"])
    try:
        for lib in libs[::-1]:
            conf.env["LIBS"].insert(0, lib)
        ret = create_link_conf_taskgen(conf, "check_func", body,
                            None, "Checking for functions %s" \
                                  % ", ".join(funcs))
    finally:
        conf.env["LIBS"] = old_lib

    for func in funcs:
        conf.conf_results.append({"type": "func", "value": func,
                                  "result": ret})
    return ret
