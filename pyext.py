import distutils.sysconfig

from cPickle \
    import \
        load, dump, dumps

from ctasks \
    import \
        link_task
from task_manager \
    import \
        get_bld, create_tasks, topo_sort, build_dag, run_tasks, CACHE_FILE

# import necessary to register ".in" hook
import tpl_tasks

def create_pyext(bld, name, sources):
    base = name.split(".")[-1]

    tasks = []

    cpppaths = bld.env["CPPPATH"]
    pyinc = distutils.sysconfig.get_python_inc()
    cpppaths.append(pyinc)
    bld.env["INCPATH"] = " ".join(["-I%s" % p
                                    for p in cpppaths])

    tasks = create_tasks(bld, sources)
    tasks.append(link_task(bld, name.split(".")[-1]))

    tuid_to_task = dict([(t.get_uid(), t) for t in tasks])

    task_deps, output_to_tuid = build_dag(tasks)

    yo = topo_sort(task_deps)
    ordered_tasks = []
    for output in yo:
        if output in output_to_tuid:
            ordered_tasks.append(tuid_to_task[output_to_tuid[output]])

    for t in tasks:
        t.env = bld.env

    run_tasks(bld, ordered_tasks)

def create_sources(bld, name, sources):
    tasks = create_tasks(bld, sources)
    run_tasks(bld, tasks)

if __name__ == "__main__":
    bld = get_bld()
    bld.env = {"CC": ["gcc"],
            "CFLAGS": ["-W"],
            "CPPPATH": [],
            "SHLINK": ["gcc", "-O1"],
            "SHLINKFLAGS": ["-shared", "-g"],
            "SUBST_DICT": {"VERSION": "0.0.2"},
    }

    create_sources(bld, "template", sources=["foo.h.in"])
    create_pyext(bld, "_bar", ["hellomodule.c", "foo.c"])

    with open(CACHE_FILE, "w") as fid:
        dump(bld.cache, fid)
