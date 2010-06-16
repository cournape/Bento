def detect(ctx):
    env = ctx.env

    ctx.env["CC"] = ["gcc"]
    ctx.env["CC_TGT_F"] = ["-c", "-o"]
    ctx.env["CC_SRC_F"] = []
    ctx.env["CFLAGS"] = ["-Wall"]
    ctx.env["LINK"] = ["gcc"]
    ctx.env["LINKFLAGS"] = []
    ctx.env["LINK_TGT_F"] = ["-o"]
    ctx.env["LINK_SRC_F"] = []
    ctx.env["SHLINK"] = ["gcc", "-shared"]
    ctx.env["SHLINKFLAGS"] = []
    ctx.env["CPPPATH"] = []
    ctx.env["CPPPATH_FMT"] = "-I%s"
    ctx.env["LIBDIR"] = []
    ctx.env["LIBS"] = []
    ctx.env["LIB_FMT"] = "-l%s"
    ctx.env["LIBDIR_FMT"] = "-L%s"

    ctx.env["CC_OBJECT_FMT"] = "%s.o"
    ctx.env["PROGRAM_FMT"] = "%s"
