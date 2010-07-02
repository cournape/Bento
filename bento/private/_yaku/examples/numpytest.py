import os

from yaku.utils \
    import \
        ensure_dir
from yaku.context \
    import \
        get_cfg
from yaku.conftests \
    import \
        check_compiler, check_header, check_func, check_lib, check_type, \
        generate_config_h, check_type_size, define, check_funcs_at_once

def configure(conf):
    conf.use_tools(["ctasks"])

    log_filename = os.path.join("build", "config.log")
    ensure_dir(log_filename)

    conf.log = open(log_filename, "w")
    try:
        check_compiler(conf)
        conf.env["CPPPATH"].append("/usr/include/python2.6")
        if not check_header(conf, "Python.h"):
            raise RuntimeError("Python header not found !")
        check_header(conf, "math.h")
        for mlibs in [[], ["m"]]:
            if check_func(conf, "floor", libs=mlibs):
                break
        for tp in ("short", "int", "long"):
            check_type_size(conf, tp)
        for tp in ("float", "double", "long double"):
            check_type_size(conf, tp)
        check_type(conf, "Py_intptr_t", headers=["Python.h"])
        define(conf, "NPY_NO_SMP")

        mfuncs = ('expl', 'expf', 'log1p', 'expm1', 'asinh', 'atanhf',
                'atanhl', 'rint', 'trunc')
        check_funcs_at_once(conf, mfuncs)
        generate_config_h(conf.conf_results, "build/conf/config.h")
    finally:
        conf.log.close()

if __name__ == "__main__":
    ctx = get_cfg()
    configure(ctx)
    ctx.store()
