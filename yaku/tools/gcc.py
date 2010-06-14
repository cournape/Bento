def detect(ctx):
    env = ctx.env

    ctx.env["CC"] = ["gcc"]
    ctx.env["CC_TGT_F"] = ["-c", "-o"]
    ctx.env["CC_TGT_G"] = ["-c", "-o"]
    ctx.env["CFLAGS"] = ["-Wall"]
    ctx.env["LINK"] = ["gcc"]
    ctx.env["LINKFLAGS"] = []
    ctx.env["SHLINK"] = ["gcc", "-shared"]
    ctx.env["SHLINKFLAGS"] = []
    ctx.env["CPPPATH"] = []
    ctx.env["LIBDIR"] = []
    ctx.env["LIBS"] = []
    ctx.env["LIB_FMT"] = "-l%s"
    ctx.env["LIBDIR_FMT"] = "-L%s"
