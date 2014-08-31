import os

from yaku.environment \
    import \
        Environment

RULES_REGISTRY = {}
FILES_REGISTRY = {}

def extension(ext):
    def _f(f):
        RULES_REGISTRY[ext] = f
        return f
    return _f

def set_extension_hook(ext, hook):
    old = RULES_REGISTRY.get(ext, None)
    RULES_REGISTRY[ext] = hook
    return old

def wrap_extension_hook(ext, hook_factory):
    old = RULES_REGISTRY.get(ext, None)
    RULES_REGISTRY[ext] = hook_factory(old)
    return old

def get_extension_hook(ext):
    try:
        return RULES_REGISTRY[ext]
    except KeyError:
        raise ValueError("No hook registered for extension %r" % ext)

def set_file_hook(ctx, source, hook):
    node = ctx.src_root.find_resource(source)
    if node is None:
        raise IOError("file %s not found" % source)
    FILES_REGISTRY[node] = hook

class NoHookException(Exception):
    pass

def hash_task(t):
    # FIXME: ext_in and ext_out should not be computed from the files
    ext_in = [os.path.splitext(s.name)[1] for s in t.inputs]
    ext_out = [os.path.splitext(s.name)[1] for s in t.outputs]
    tup = tuple(ext_in + ext_out + t.before + t.after)
    return hash((t.__class__.__name__, tup))

class TaskManager(object):
    def __init__(self, tasks):
        self.tasks = tasks

        self.groups = {}
        self.order = {}
        self.make_groups()
        self.make_order()

    def set_order(self, a, b):
        if not a in self.order:
            self.order[a] = set()
        self.order[a].add(b)

    def make_order(self):
        keys = list(self.groups.keys())
        max = len(keys)
        for i in range(max):
            t1 = self.groups[keys[i]][0]
            for j in range(i + 1, max):
                t2 = self.groups[keys[j]][0]

                if t2.__class__.__name__ in t1.before:
                    self.set_order(keys[j], keys[i])
                elif t1.__class__.__name__ in t2.before:
                    self.set_order(keys[i], keys[j])
                else:
                    # add the constraints based on the comparisons
                    val = self.compare_exts(t1, t2)
                    if val > 0:
                        self.set_order(keys[i], keys[j])
                    elif val < 0:
                        self.set_order(keys[j], keys[i])

    def make_groups(self):
        # XXX: we assume tasks with same input/output suffix can run
        # in // (naive emulation of csr-like scheduler in waf)
        groups = self.groups
        for t in self.tasks:
            h = hash_task(t)
            if h in groups:
                groups[h].append(t)
            else:
                groups[h] = [t]

    def next_set(self):
        keys = self.groups.keys()

        unconnected = []
        remainder = []

        for u in keys:
            for k in self.order.values():
                if u in k:
                    remainder.append(u)
                    break
            else:
                unconnected.append(u)

        toreturn = []
        for y in unconnected:
            toreturn.extend(self.groups[y])

        # remove stuff only after
        for y in unconnected:
                try:
                    self.order.__delitem__(y)
                except KeyError:
                    pass
                self.groups.__delitem__(y)

        if not toreturn and remainder:
            raise Exception("circular order constraint detected %r" % remainder)

        return toreturn


    def compare_exts(self, t1, t2):
        "extension production"
        def _get_in(t):
            return [os.path.splitext(s.name)[1] for s in t.inputs]
        def _get_out(t):
            return [os.path.splitext(s.name)[1] for s in t.outputs]

        in_ = _get_in(t1)
        out_ = _get_out(t2)
        for k in in_:
            if k in out_:
                return -1
        in_ = _get_in(t2)
        out_ = _get_out(t1)
        for k in in_:
            if k in out_:
                return 1
        return 0

def run_task(ctx, task):
    def _run(t):
        t.run()
        ctx.cache[tuid] = t.signature()

    tuid = task.get_uid()
    # XXX: there may be a better way to do this without stating output
    # (we want to know if the task has already been executed in a
    # previous run)
    for o in task.outputs:
        if not os.path.exists(o.abspath()):
            _run(task)
            break
    if not tuid in ctx.cache:
        _run(task)
    else:
        sig = task.signature()
        if sig != ctx.cache[tuid]:
            _run(task)

def build_dag(tasks):
    # Build dependency graph (DAG)
    # task_deps[target] = list_of_dependencies
    # At this point, task_deps is not guaranteed to be a DAG (may have
    # cycle) - will be detected during topological sort
    task_deps = {}
    output_to_tuid = {}
    for t in tasks:
        for o in t.outputs:
            try:
                task_deps[o].extend(t.inputs + t.deps)
            except KeyError:
                task_deps[o] = t.inputs[:] + t.deps[:]
            output_to_tuid[o] = t.get_uid()
    return task_deps, output_to_tuid

def topo_sort(task_deps):
    # Topological sort (depth-first search)
    # XXX: cycle detection is missing
    tmp = []
    nodes = []
    for dep in task_deps.values():
        nodes.extend(dep)
    nodes.extend(task_deps.keys())
    nodes = set(nodes)

    visited = set()
    def visit(node):
        if not node in visited:
           visited.add(node)
           deps = task_deps.get(node, None)
           if deps:
               for c in deps:
                   visit(c)
           tmp.append(node)

    for node in nodes:
        visit(node)

    return tmp

def _get_hook(source):
    if source in FILES_REGISTRY:
        return FILES_REGISTRY[source]
    for ext in RULES_REGISTRY:
        if source.name.endswith(ext):
            return RULES_REGISTRY[ext]
    raise NoHookException(
            "No rule defined for extension %r" % source.suffix())

class TaskGen(object):
    def __init__(self, name, bld, sources, target):
        self.bld = bld
        self.name = name
        self.sources = sources
        self.target = target

        self.env = Environment()

    def process(self):
        tasks = []
        for s in self.sources:
            f = _get_hook(s)
            tsks = f(self, s)
            tasks.extend(tsks)
        return tasks

class CompiledTaskGen(TaskGen):
    def __init__(self, name, bld, sources, target):
        TaskGen.__init__(self, name, bld, sources, target)
        self.object_tasks = []
        self.link_task = None
        self.has_cxx = False

    def add_objects(self, tasks):
        """Add new object tasks, assuming the link task has already
        been defined."""
        if self.link_task is None:
            raise ValueError("You cannot add object nodes "
                             "before setting the link task !")
        else:
            self.object_tasks += tasks

def order_tasks(tasks):
    tuid_to_task = dict([(t.get_uid(), t) for t in tasks])

    task_deps, output_to_tuid = build_dag(tasks)

    yo = topo_sort(task_deps)
    ordered_tasks = []
    for output in yo:
        if output in output_to_tuid:
            ordered_tasks.append(tuid_to_task[output_to_tuid[output]])

    return ordered_tasks

