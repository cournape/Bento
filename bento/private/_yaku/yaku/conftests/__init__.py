import sys
import re

if sys.version_info[0] < 3:
    from cStringIO \
        import \
            StringIO
else:
    from io \
        import \
            StringIO

from yaku.utils \
    import \
        ensure_dir
from yaku.conftests.conftests \
    import \
       check_compiler, check_type, check_header, check_func, \
       check_lib, check_type_size, define, check_funcs_at_once, check_cpp_symbol

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
