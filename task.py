import re
import subprocess
import distutils.sysconfig
import os
from hashlib import md5

from cPickle \
    import \
        load, dump, dumps

from toydist.core.utils \
    import \
        pprint

from utils \
    import \
        find_deps

VARS = {"cc": ["CC", "CFLAGS"],
        "cc_link": ["SHLINK", "SHLINKFLAGS"],
        "template": ["SUBST_DICT"]}

class Task(object):
    def __init__(self, name, outputs, inputs, func=None, deps=None):
        if isinstance(inputs, basestring):
            self.inputs = [inputs]
        else:
            self.inputs = inputs
        if isinstance(outputs, basestring):
            self.outputs = [outputs]
        else:
            self.outputs = outputs
        self.name = name or ""
        self.uid = None
        self.func = func
        if deps is None:
            self.deps = []
        else:
            self.deps = deps
        self.cache = None
        self.env = None
        self.env_vars = None
        self.scan = None

    # UID and signature functionalities
    #----------------------------------
    def get_uid(self):
        if self.uid is None:
            m = md5()
            up = m.update
            up(self.__class__.__name__)
            for x in self.inputs + self.outputs:
                up(x)
            self.uid = m.digest()
        return self.uid

    def signature(self):
        if self.cache is None:
            sig = self._signature()
            self.cache = sig
            return sig
        else:
            return self.cache

    def _signature(self):
        m = md5()

        self._sig_explicit_deps(m)
        for k in self.env_vars:
            m.update(dumps(self.env[k]))
        return m.digest()

    def _sig_explicit_deps(self, m):
        for s in self.inputs + self.deps + self.outputs:
            #if os.path.exists(s):
            #    m.update(open(s).read())
            m.update(open(s).read())
        return m.digest()
        
    # execution
    #----------
    def run(self):
        self.func(self)

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

def template(self):
    if not len(self.inputs) == 1:
        raise ValueError("template func needs exactly one input")
    pprint('GREEN', "TEMPLATE   %s" % self.inputs[0])

    subs_re = dict([(k, re.compile("@" + k + "@")) 
                     for k in self.env["SUBST_DICT"]])
    with open(self.inputs[0]) as fid:
        cnt = fid.read()
        for k, v in self.env["SUBST_DICT"].items():
            cnt = subs_re[k].sub(v, cnt)

    with open(self.outputs[0], "w") as fid:
        fid.write(cnt)

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

def template_task(self, node):
    base = os.path.splitext(node)[0]
    target = base
    task = Task("template", inputs=node, outputs=target)
    task.func = template
    task.env_vars = VARS["template"]
    task.env = self.env
    return task
