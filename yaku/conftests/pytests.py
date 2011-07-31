import sys

def check_module(conf, module_name):
    conf.start_message("Checking for module %r" % (module_name,))
    python = sys.executable
    cmd = [python, "-c", "'import %s'" % module_name]
    ret = conf.try_command(" ".join(cmd), kw={"shell": True})
    if ret:
        conf.end_message("yes")
    else:
        conf.end_message("no")
    return ret
