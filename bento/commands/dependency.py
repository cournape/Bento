from collections \
    import \
        defaultdict
from cPickle \
    import \
        dump, load, dumps

try:
    from hashlib import md5
except ImportError:
    from md5 import md5

class PickledStore(object):
    """Simple class to store/retrieve data from a pickled file."""
    @classmethod
    def from_dump(cls, filename):
        with open(filename, "rb") as fid:
            data = load(fid)

        inst = cls()
        inst._data = data
        return inst

    def store(self, filename):
        with open(filename, "wb") as fid:
            dump(self._data, fid)

class TaskStore(PickledStore):
    def __init__(self):
        super(TaskStore, self).__init__()
        self._data = {}

    def set(self, k, v):
        self._data[k] = v

    def get(self, k):
        return self._data[k]

class CommandTask(object):
    def __init__(self, cmd_name):
        self._uid = None
        self._sig = None
        self.cmd_name = cmd_name
        self.data_deps = {}

    def set_dependencies(self, **kw):
        for k, v in kw.iteritems():
            self.data_deps[k] = v

    def signature(self):
        if self._sig is None:
            m = md5()
            m.update(dumps(self.data_deps))
            self._sig = m.digest()
        return self._sig

    def uid(self):
        # XXX: normally, we don't expect to have multiple instances of the same
        # cmd class. Cannot use python id, as we want the same id to be
        # deterministic across runs
        if self._uid is None:
            m = md5()
            m.update(self.__class__.__name__.encode())
            m.update(self.cmd_name)
            self._uid = m.digest()
        return self._uid

    # XXX: Each command should have a data dict associated to it, with data on
    # which it depends
    def store_state(self, cmd_data):
        cmd_data.set(self.uid(), self.env)

    def up_to_date(self, signature_cache):
        try:
            cached_sig = signature_cache.get(self)
            return self.signature() == cached_sig
        except KeyError:
            return False

def _invert_dependencies(deps):
    """Given a dictionary of edge -> dependencies representing a DAG, "invert"
    all the dependencies."""
    ideps = {}
    for k, v in deps.items():
        for d in v:
            l = ideps.get(d, None)
            if l:
                l.append(k)
            else:
                l = [k]
            ideps[d] = l

    return ideps

class CommandScheduler(object):
    def __init__(self):
        self.before = defaultdict(list)
        self.klasses = []

    def register(self, klass):
        if not klass.__name__ in self.klasses:
            self.klasses.append(klass.__name__)

    def set_before(self, klass, klass_prev):
        """Set klass_prev to be run before klass"""
        self.register(klass)
        self.register(klass_prev)
        klass_name = klass.__name__
        klass_prev_name = klass_prev.__name__
        if not klass_prev_name in self.before[klass_name]:
            self.before[klass_name].append(klass_prev_name)

    def set_after(self, klass, klass_next):
        """Set klass_next to be run after klass"""
        return self.set_before(klass_next, klass)

    def order(self, target):
        # XXX: cycle detection missing !
        after = _invert_dependencies(self.before)

        visited = {}
        out = []

        # DFS-based topological sort: this is better to only get the
        # dependencies of a given target command instead of sorting the whole
        # dag
        def _visit(n, stack_visited):
            if n in stack_visited:
                raise ValueError("Cycle detected: %r" % after)
            else:
                stack_visited[n] = None
            if not n in visited:
                visited[n] = None
                for m, v in after.items():
                    if n in v:
                        _visit(m, stack_visited)
                out.append(n)
            stack_visited.pop(n)
        _visit(target.__name__, {})
        return out
