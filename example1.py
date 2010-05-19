import sys

from cPickle \
    import \
        dump

from yaku.pyext \
    import \
        create_pyext, get_pyenv

from yaku.task_manager \
    import \
        get_bld, CACHE_FILE
from yaku.tools \
    import \
        import_tools

import_tools(["ctasks"], ["tools"])

if __name__ == "__main__":
    from yaku.tools.gcc import detect as gcc_detect

    bld = get_bld()
    bld.env.update({
            "VERBOSE": False,
            "BLDDIR": "build"})
    if "-v" in sys.argv:
        bld.env["VERBOSE"] = True
    bld.env.update(get_pyenv())
    gcc_detect(bld)

    create_pyext(bld, "_bar", ["src/hellomodule.c"])

    with open(CACHE_FILE, "w") as fid:
        dump(bld.cache, fid)
