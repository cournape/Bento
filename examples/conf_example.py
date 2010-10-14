import os

from yaku.utils \
    import \
        ensure_dir
from yaku.context \
    import \
        get_cfg
from yaku.conftests \
    import \
        check_compiler, check_header, check_func, check_lib, check_type, generate_config_h

def configure(conf):
    conf.use_tools(["ctasks"])

    log_filename = os.path.join("build", "config.log")
    ensure_dir(log_filename)

    conf.log = open(log_filename, "w")
    try:
        # TODO
        #  - support for env update
        #  - config header support
        #  - confdefs header support
        check_compiler(conf)
        check_header(conf, "stdio.h")
        check_header(conf, "stdio")
        check_type(conf, "char")
        #check_type(conf, "complex")
        check_type(conf, "complex", headers=["complex.h"])
        if check_func(conf, "exp"):
            mlib = []
        else:
            if not check_lib(conf, "m", "exp"):
                raise ValueError("What is mlib ?")
            else:
                mlib = ["m"]
        check_lib(conf, mlib, "exp")
        #check_lib(conf, lib="mm")
        check_func(conf, "floor", libs=mlib)
        check_func(conf, "floor")

        generate_config_h(conf.conf_results, "build/conf/config.h")
    finally:
        conf.log.close()

if __name__ == "__main__":
    ctx = get_cfg()
    configure(ctx)
    ctx.store()
