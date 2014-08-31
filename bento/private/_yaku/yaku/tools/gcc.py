import yaku.utils

def setup(ctx):
    env = ctx.env

    ctx.env["CC"] = ["gcc"]
    ctx.env["CC_TGT_F"] = ["-c", "-o"]
    ctx.env["CC_SRC_F"] = []
    ctx.env["CFLAGS"] = ["-Wall"]
    ctx.env["CFLAGS_SH"] = ["-fPIC"]
    ctx.env["DEFINES"] = []
    ctx.env["DEFINES_FMT"] = "-D%s"
    ctx.env["LINK"] = ["gcc"]
    ctx.env["LINKFLAGS"] = []
    ctx.env["LINK_TGT_F"] = ["-o"]
    ctx.env["LINK_SRC_F"] = []
    ctx.env["SHAREDLIB_FMT"] = "lib%s.so"
    ctx.env["SHLINK"] = ["gcc", "-shared"]
    ctx.env["SHLINKFLAGS"] = []
    ctx.env["SHLINK_TGT_F"] = ["-o"]
    ctx.env["SHLINK_SRC_F"] = []
    ctx.env["MODLINK"] = ["gcc", "-bundle", "-undefined", "dynamic_lookup"]
    ctx.env["MODLINKFLAGS"] = []
    ctx.env["MODLINK_TGT_F"] = ["-o"]
    ctx.env["MODLINK_SRC_F"] = []
    ctx.env["CPPPATH"] = []
    ctx.env["CPPPATH_FMT"] = "-I%s"
    ctx.env["LIBDIR"] = []
    ctx.env["LIBS"] = []
    ctx.env["FRAMEWORKS"] = []
    ctx.env["LIB_FMT"] = "-l%s"
    ctx.env["LIBDIR_FMT"] = "-L%s"

    ctx.env["CC_OBJECT_FMT"] = "%s.o"
    ctx.env["PROGRAM_FMT"] = "%s"

def detect(ctx):
    if yaku.utils.find_program("gcc") is None:
        return False
    else:
        return True
