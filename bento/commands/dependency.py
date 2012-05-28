import os
import sys

from six.moves import cPickle

from bento.compat.api \
    import \
        defaultdict
import bento.utils.io2

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
        self.command_names = {}

    def _register(self, command_name):
        if not command_name in self.command_names:
            self.command_names[command_name] = command_name

    def set_before(self, command_name, command_name_prev):
        """Set command_name_prev to be run before command_name"""
        self._register(command_name)
        self._register(command_name_prev)
        if not command_name_prev in self.before[command_name]:
            self.before[command_name].append(command_name_prev)

    def set_after(self, command_name, command_name_next):
        """Set command_name_next to be run after command_name"""
        return self.set_before(command_name_next, command_name)

    def order(self, target):
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
        _visit(target, {})
        return [self.command_names[o] for o in out[:-1]]

class CommandDataProvider(object):
    @classmethod
    def from_file(cls, filename):
        """Create a new instance from a pickled file.

        If the file does not exist, creates an instance with no data.
        """
        if os.path.exists(filename):
            fid = open(filename, "rb")
            try:
                return cls(cPickle.load(fid))
            finally:
                fid.close()
        else:
            return cls()

    def store(self, filename):
        bento.utils.io2.safe_write(filename, lambda fid: cPickle.dump(self._data, fid))

    def __init__(self, data=None):
        self._data = defaultdict(list)
        if data:
            self._data.update(data)

    def __getitem__(self, command_name):
        return self._data[command_name]

    def __setitem__(self, command_name, command_argv):
        self._data[command_name] = command_argv
