import os
import re

try:
    from hashlib import md5
except ImportError:
    from md5 import md5

from cStringIO \
    import \
        StringIO

from yaku.errors \
    import \
        UnknownTask
from yaku.utils \
    import \
        ensure_dir

def create_file(conf, code, prefix="", suffix=""):
    filename = "%s%s%s" % (prefix, md5(code.encode()).hexdigest(), suffix)
    node = conf.bld_root.declare(filename)
    node.write(code)
    return node

def with_conf_blddir(conf, name, body, func):
    """'Context manager' to execute a series of tasks into code-specific build
    directory.
    
    func must be a callable taking no arguments
    """
    old_root, new_root = create_conf_blddir(conf, name, body)
    try:
        conf.bld_root = new_root
        return func()
    finally:
        conf.bld_root = old_root

def write_log(conf, log, tasks, code, succeed, explanation):
    for line in code.splitlines():
        log.write("  |%s\n" % line)

    if succeed:
        log.write("---> Succeeded !\n")
    else:
        log.write("---> Failure !\n")
        log.write("~~~~~~~~~~~~~~\n")
        log.write(explanation)
        log.write("~~~~~~~~~~~~~~\n")

    s = StringIO()
    s.write("Command sequence was:\n")
    for t in tasks:
        try:
            cmd = conf.get_cmd(t)
            s.write("%s\n" % " ".join(cmd))
            stdout = conf.get_stdout(t)
            if stdout:
                s.write("\n")
                for line in stdout.splitlines():
                    s.write("%s\n" % line)
                s.write("\n")
        except UnknownTask:
            break
    log.write(s.getvalue())
    log.write("\n")

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

def create_conf_blddir(conf, name, body):
    dirname = ".conf-%s-%s" % (name, hash(name+body))
    bld_root = os.path.join(conf.bld_root.abspath(), dirname)
    if not os.path.exists(bld_root):
        os.makedirs(bld_root)
    bld_root = conf.bld_root.make_node(dirname)
    old_root = conf.bld_root
    return old_root, bld_root
