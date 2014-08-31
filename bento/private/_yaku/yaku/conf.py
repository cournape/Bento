import os
import sys
import re

try:
    from hashlib import md5
except ImportError:
    from md5 import md5

if sys.version_info[0] < 3:
    from cStringIO \
        import \
            StringIO
else:
    from io \
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
        conf.bld_root.ctx.bldnode = new_root
        return func()
    finally:
        conf.bld_root = old_root
        conf.bld_root.ctx.bldnode = old_root

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

def create_conf_blddir(conf, name, body):
    dirname = ".conf-%s-%s" % (name, hash(name+body))
    bld_root = os.path.join(conf.bld_root.abspath(), dirname)
    if not os.path.exists(bld_root):
        os.makedirs(bld_root)
    bld_root = conf.bld_root.make_node(dirname)
    old_root = conf.bld_root
    return old_root, bld_root
