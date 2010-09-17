import sys
import os

from yaku.context \
    import \
        get_bld, get_cfg
import yaku.errors

from pprint import pprint

def get_clang_env(ctx):
    from distutils.sysconfig import get_config_var, get_python_inc
    env = {
            "CC": ["clang"],
            "CPPPATH": [get_python_inc()],
            "BASE_CFLAGS": ["-fno-strict-aliasing"],
            "OPT": ["-O2", "-Wall"],
            "SHARED": ["-fPIC"],
            "SHLINK": ["clang"],
            "LIBDIR": [],
            "LIBS": [],
            "SO": ".so",
            "LDFLAGS": []
            }

    if sys.platform == "darwin":
        env["LDFLAGS"].extend(["-bundle", "-undefined", "dynamic_lookup"])
    else:
        env["LDFLAGS"].append("-shared")
    return env

def pyext_configure(ctx, compiler_type="default"):
    # How we do it
    # - query distutils C compiler ($CC variable)
    # - try to determine yaku tool name from $CC
    # - get options from sysconfig
    # - apply necessary variables from yaku tool to $PYEXT_
    # "namespace"

    from yaku.sysconfig import detect_distutils_cc
    from yaku.tools.pyext import detect_cc_type, setup_pyext_env

    if True:
        dist_env = setup_pyext_env(ctx)
        ctx.env.update(dist_env)
    else:
        compiler_type = "clang"
        dist_env = get_clang_env(ctx)
        for name, value in dist_env.items():
            ctx.env["PYEXT_%s" % name] = value
        ctx.env["PYEXT_FMT"] = "%%s%s" % dist_env["SO"]
        ctx.env["PYEXT_CFLAGS"] = ctx.env["PYEXT_BASE_CFLAGS"] + \
                ctx.env["PYEXT_OPT"] + \
                ctx.env["PYEXT_SHARED"]
        ctx.env["PYEXT_SHLINKFLAGS"] = dist_env["LDFLAGS"]

    if compiler_type == "default":
        cc = detect_distutils_cc(ctx)
        cc_type = detect_cc_type(ctx, cc)
    else:
        cc_type = compiler_type

    old_env = ctx.env
    ctx.env = {}
    sys.path.insert(0, os.path.dirname(yaku.tools.__file__))
    try:
        try:
            mod = __import__(cc_type)
            mod.setup(ctx)
        except ImportError:
            raise RuntimeError("No tool %s is available (import failed)" \
                            % cc_type)

        # XXX: this is ugly - find a way to have tool-specific env...
        cc_env = ctx.env
        ctx.env = old_env
        TRANSFER = ["CPPPATH_FMT", "LIBDIR_FMT", "LIB_FMT", "CC_OBJECT_FMT", "CC_TGT_F", "CC_SRC_F", "LINK_TGT_F", "LINK_SRC_F"]
        for k in TRANSFER:
            ctx.env["PYEXT_%s" % k] = cc_env[k]
    finally:
        sys.path.pop(0)

def configure(ctx):
    ctx.load_tool("ctasks")
    ctx.load_tool("pyext")
    ctx._tool_modules["pyext"].configure = pyext_configure

def build(ctx):
    ctx.builders["pyext"].extension("_bar", 
            [os.path.join("src", "hellomodule.c")])
    from yaku.scheduler import SerialRunner
    from yaku.task_manager import TaskManager
    runner = SerialRunner(ctx, TaskManager(ctx.tasks))
    runner.start()
    runner.run()

if __name__ == "__main__":
    ctx = get_cfg()
    configure(ctx)
    ctx.setup_tools()
    ctx.store()

    ctx = get_bld()
    build(ctx)
    ctx.store()
