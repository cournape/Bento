import os

from cPickle \
    import \
        load, dump

from yaku.utils \
    import \
        ensure_dir
from yaku.conf \
    import \
        ConfigureContext
from yaku.conftests \
    import \
        check_compiler, check_header, check_func, check_lib, check_type, generate_config_h

CONF_CACHE_FILE = ".conf.cpk"

if __name__ == "__main__":
    from yaku.tools.gcc import detect

    # TODO
    #  - support for env update
    #  - config header support
    #  - confdefs header support
    conf = ConfigureContext()
    if os.path.exists(CONF_CACHE_FILE):
        with open(CONF_CACHE_FILE) as fid:
            conf.cache = load(fid)

    detect(conf)
    conf.env.update({"LIBDIR": [], "LIBS": [],
        "BLDDIR": "build/conf",
        "VERBOSE": False})
    log_filename = os.path.join("build", "config.log")
    ensure_dir(log_filename)
    conf.log = open(log_filename, "w")

    check_compiler(conf)
    check_header(conf, "stdio.h")
    check_header(conf, "stdio")
    check_type(conf, "char")
    #check_type(conf, "complex")
    check_type(conf, "complex", headers=["complex.h"])
    check_lib(conf, lib="m")
    #check_lib(conf, lib="mm")
    check_func(conf, "floor", libs=["m"])
    check_func(conf, "floor")

    generate_config_h(conf.conf_results, "build/conf/config.h")

    conf.log.close()
    with open(CONF_CACHE_FILE, "w") as fid:
        dump(conf.cache, fid)
