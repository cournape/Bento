def detect(ctx):
    env = ctx.env

    ctx.env.update(
       {"CC": ["gcc"],
        "CFLAGS": ["-Wall"],
        "LINK": ["gcc"],
        "LINKFLAGS": [],
        "SHLINK": ["gcc", "-shared"],
        "SHLINKFLAGS": [],
        "LIBS_FMT": "-l%s",
        "LIBPATH_FMT": "-L%s"})
