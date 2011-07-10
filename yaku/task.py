import os
import sys
try:
    from hashlib import md5
except ImportError:
    from md5 import md5
import subprocess

if sys.version_info[0] < 3:
    from cPickle \
        import \
            dumps
else:
    from pickle \
        import \
            dumps

from yaku.pprint \
    import \
        pprint
from yaku.utils \
    import \
        get_exception, is_string, function_code
from yaku.errors \
    import \
        TaskRunFailure, WindowsError

# TODO:
#   - factory for tasks, so that tasks can be created from strings
#   instead of import (import not extensible)

# Task factory - taken from waf, to avoid metaclasses magic
class _TaskFakeMetaclass(type):
    def __init__(cls, name, bases, d):
        super(_TaskFakeMetaclass, cls).__init__(name, bases, d)
        name = cls.__name__

_CLASSES = {}
def task_factory(name):
    global _CLASSES
    try:
        klass = _CLASSES[name]
    except KeyError:
        klass = _TaskFakeMetaclass('%sTask' % name, (_Task,), {})
        klass.name = name
        _CLASSES[name] = klass
    return klass

base = _TaskFakeMetaclass('__task_base', (object,), {})

class _Task(object):
    before = []
    after = []
    def __init__(self, outputs, inputs, func=None, deps=None, env=None, env_vars=None):
        if is_string(inputs):
            self.inputs = [inputs]
        else:
            self.inputs = inputs
        if is_string(outputs):
            self.outputs = [outputs]
        else:
            self.outputs = outputs
        self.uid = None
        self.func = func
        if deps is None:
            self.deps = []
        else:
            self.deps = deps
        self.cache = None
        self.env = env
        self.env_vars = env_vars
        self.scan = None
        self.disable_output = False
        self.log = None

    # UID and signature functionalities
    #----------------------------------
    def get_uid(self):
        if self.uid is None:
            m = md5()
            up = m.update
            up(self.__class__.__name__.encode())
            for x in self.inputs + self.outputs:
                up(x.abspath().encode())
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
        if self.func:
            m.update(function_code(self.func).co_code)
        return m.digest()

    def _sig_explicit_deps(self, m):
        for s in self.inputs + self.deps:
            #if os.path.exists(s):
            #    m.update(open(s).read())
            m.update(s.read(flags="rb"))
        return m.digest()
        
    # execution
    #----------
    def run(self):
        self.func(self)

    def exec_command(self, cmd, cwd, env=None):
        if cwd is None:
            cwd = self.gen.bld.bld_root.abspath()
        kw = {}
        if env is not None:
            kw["env"] = env
        if not self.disable_output:
            if self.env["VERBOSE"]:
                pprint('GREEN', " ".join([str(c) for c in cmd]))
            else:
                pprint('GREEN', "%-16s%s" % (self.name.upper(), " ".join([i.bldpath() for i in self.inputs])))

        self.gen.bld.set_cmd_cache(self, cmd)
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, cwd=cwd, **kw)
            stdout = p.communicate()[0].decode("utf-8")
            if p.returncode:
                raise TaskRunFailure(cmd, stdout)
            if sys.version_info >= (3,):
                stdout = stdout
            else:
                stdout = stdout.encode("utf-8")
            if self.disable_output:
                self.log.write(stdout)
            else:
                sys.stderr.write(stdout)
            self.gen.bld.set_stdout_cache(self, stdout)
        except OSError:
            e = get_exception()
            raise TaskRunFailure(cmd, str(e))
        except WindowsError:
            e = get_exception()
            raise TaskRunFailure(cmd, str(e))

    def __repr__(self):
        ins = ",".join([i.name for i in self.inputs])
        outs = ",".join([i.name for i in self.outputs])
        return "'%s: %s -> %s'" % (self.name, ins, outs)
