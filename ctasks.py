import os
import distutils.sysconfig
import subprocess

from toydist.core.utils \
    import \
        pprint

from task \
    import \
        Task
from task_manager \
    import \
        extension
from utils \
    import \
        find_deps

VARS = {"cc": ["CC", "CFLAGS"],
        "cc_link": ["SHLINK", "SHLINKFLAGS"]}

@extension('.c')
def ccompile_task(self, node):
    base = os.path.splitext(node)[0]
    target = base + ".o"
    task = Task("cc", inputs=node, outputs=target)
    task.func = ccompile
    task.env_vars = VARS["cc"]
    #print find_deps("foo.c", ["."])
    task.scan = lambda : find_deps(node, ["."])
    task.deps.extend(task.scan())
    self.object_tasks.append(task)
    return task

def link_task(self, name):
    objects = [tsk.outputs[0] for tsk in self.object_tasks]
    target = name + ".so"
    task = Task("cc_link", inputs=objects, outputs=target)
    task.func = shlib_link
    task.env_vars = VARS["cc_link"]
    return task

def ccompile(self, silent=True):
    pyinc = distutils.sysconfig.get_python_inc()
    incpaths = [pyinc]
    cmd = self.env["CC"] + self.env["CFLAGS"] + \
           ["-c", self.inputs[0]] + ["-o", self.outputs[0]]
    cmd += ["-I%s" % i for i in incpaths]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    if not silent:
        print " ".join(cmd)
    else:
        pprint('GREEN', "CC     %s" % " ".join(self.inputs))
    stdout, stderr = p.communicate()
    if p.returncode:
        raise ValueError("cmd %s failed: %s" % (" ".join(cmd), stderr))

def shlib_link(self, silent=True):
    cmd = ["cc", "-shared"] + self.inputs + ["-o", self.outputs[0]]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    if not silent:
        print " ".join(cmd)
    else:
        pprint('GREEN', "SHLINK %s" % " ".join(self.inputs))
    stdout, stderr = p.communicate()
    if p.returncode:
        raise ValueError("cmd %s failed: %s" % (" ".join(cmd), stderr))

