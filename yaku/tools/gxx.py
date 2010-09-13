import yaku.utils

def setup(ctx):
    env = ctx.env

    ctx.env["CXX"] = ["g++"]
    ctx.env["CXX_TGT_F"] = ["-c", "-o"]
    ctx.env["CXX_SRC_F"] = []
    ctx.env["CXXFLAGS"] = ["-Wall"]
    ctx.env["CXXLINK"] = ["g++"]
    ctx.env["CXXLINKFLAGS"] = []
    ctx.env["CXXLINK_TGT_F"] = ["-o"]
    ctx.env["CXXLINK_SRC_F"] = []
    ctx.env["CXXSHLINK"] = ["g++", "-shared"]
    ctx.env["CXXSHLINKFLAGS"] = []
    ctx.env["CXXSHLINK_TGT_F"] = ["-o"]
    ctx.env["CXXSHLINK_SRC_F"] = []
    ctx.env["CPPPATH"] = []
    ctx.env["CPPPATH_FMT"] = "-I%s"
    ctx.env["LIBDIR"] = []
    ctx.env["LIBS"] = []
    ctx.env["FRAMEWORKS"] = []
    ctx.env["LIB_FMT"] = "-l%s"
    ctx.env["LIBDIR_FMT"] = "-L%s"

    ctx.env["CXX_OBJECT_FMT"] = "%s.o"
    ctx.env["PROGRAM_FMT"] = "%s"

def detect(ctx):
    if yaku.utils.find_program("gcc") is None:
        return False
    else:
        return True
