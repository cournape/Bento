import os

from cPickle \
    import \
        load, dump, dumps

from task import Task, template_task
from ctasks \
    import \
        ccompile_task

RULES_REGISTRY = {
        ".c": ccompile_task,
        ".in": template_task,
}

CACHE_FILE = ".cache.lock"

class BuildContext(object):
    def __init__(self):
        self.object_tasks = []
        self.cache = {}
        self.env = {}

def create_tasks(ctx, sources):
    tasks = []

    for s in sources:
        base, ext = os.path.splitext(s)
        try:
            task_gen = RULES_REGISTRY[ext]
            tasks.append(task_gen(ctx, s))
        except KeyError:
            pass
    return tasks

def run_tasks(ctx, tasks):
    def run(t):
        t.run()
        ctx.cache[tuid] = t.signature()

    for t in tasks:
        tuid = t.get_uid()
        for o in t.outputs:
            if not os.path.exists(o):
                run(t)
                break
        if not tuid in ctx.cache:
            run(t)
        else:
            sig = t.signature()
            if sig != ctx.cache[tuid]:
                run(t)

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

def get_bld():
    bld = BuildContext()
    bld.env = {"CC": ["gcc"],
            "CFLAGS": ["-W"],
            "SHLINK": ["gcc", "-O1"], 
            "SHLINKFLAGS": ["-shared", "-g"],
            "SUBST_DICT": {"VERSION": "0.0.2"},
    }

    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as fid:
            bld.cache = load(fid)
    else:
        bld.cache = {}

    return bld
