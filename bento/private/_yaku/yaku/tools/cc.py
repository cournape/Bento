def detect(ctx):
    env = ctx.env

    ctx.env["CC"] = ["cc"]
    ctx.env["CC_TGT_F"] = ["-c", "-o"]
    ctx.env["CC_SRC_F"] = []
    ctx.env["CFLAGS"] = []
    ctx.env["CPPPATH"] = []
    ctx.env["CPPPATH_FMT"] = "-I%s"
    ctx.env["LINK"] = ["cc"]
    ctx.env["LINKFLAGS"] = []
    ctx.env["LIBS"] = []
    ctx.env["LIB_FMT"] = "-l%s"
    ctx.env["LIBDIR_FMT"] = "-L%s"
