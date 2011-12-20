import os
import sys

if sys.version_info[0] < 3:
    from cPickle \
        import \
            dump, load
else:
    from pickle \
        import \
            dump, load

from bento.compat.api \
    import \
        defaultdict

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

# Instance of this class record, persist and retrieve data on a per command
# basis, to reuse them between runs. Anything refered in Command.external_deps
# need to be registered here
# It is slightly over-designed for the current use-case of storing per-command
# arguments
class CommandDataProvider(object):
    @classmethod
    def from_file(cls, filename):
        if os.path.exists(filename):
            fid = open(filename, "rb")
            try:
                cmd_argv = load(fid)
            finally:
                fid.close()
        else:
            cmd_argv = {}
        return cls(cmd_argv)

    def __init__(self, cmd_argv=None):
        if cmd_argv is None:
            cmd_argv = {}
        self._cmd_argv = cmd_argv

    def set(self, cmd_name, cmd_argv):
        self._cmd_argv[cmd_name] = cmd_argv[:]

    def get_argv(self, cmd_name):
        try:
            return self._cmd_argv[cmd_name]
        except KeyError:
            return []

    def store(self, filename):
        fid = open(filename, "wb")
        try:
            dump(self._cmd_argv, fid)
        finally:
            fid.close()
