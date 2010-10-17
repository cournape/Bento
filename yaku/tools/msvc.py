import distutils.ccompiler

import yaku.task

def _exec_command_factory(saved):
    def msvc_exec_command(self, cmd, cwd):
        new_cmd = []
        carry = ""
        for c in cmd:
            if c in ["/Fo", "/out:", "/OUT:", "/object:"]:
                carry = c
            else:
                c = carry + c
                carry = ""
                new_cmd.append(c)
        saved(self, new_cmd, cwd)
    return msvc_exec_command

def setup(ctx):
    env = ctx.env

    ctx.env["CC"] = ["cl.exe"]
    ctx.env["CC_TGT_F"] = ["/c", "/Fo"]
    ctx.env["CC_SRC_F"] = []
    ctx.env["CFLAGS"] = ["/nologo"]
    ctx.env["CPPPATH"] = []
    ctx.env["CPPPATH_FMT"] = "/I%s"
    ctx.env["LINK"] = ["link.exe"]
    ctx.env["LINK_TGT_F"] = ["/out:"]
    ctx.env["LINK_SRC_F"] = []
    ctx.env["LINKFLAGS"] = []
    ctx.env["SHLINK"] = ["link.exe"]
    ctx.env["SHLINK_TGT_F"] = ["/out:"]
    ctx.env["SHLINK_SRC_F"] = []
    ctx.env["SHLINKFLAGS"] = []
    ctx.env["LIBS"] = []
    ctx.env["LIB_FMT"] = "%s.lib"
    ctx.env["LIBDIR"] = []
    ctx.env["LIBDIR_FMT"] = "/LIBPATH:%s"

    ctx.env["CXX"] = ["cl.exe"]
    ctx.env["CXX_TGT_F"] = ["/c", "/Fo"]
    ctx.env["CXX_SRC_F"] = []
    ctx.env["CXXFLAGS"] = ["/nologo"]
    ctx.env["CXXLINK"] = ["link.exe"]
    ctx.env["CXXLINKFLAGS"] = []
    ctx.env["CXXLINK_TGT_F"] = ["/out:"]
    ctx.env["CXXLINK_SRC_F"] = []
    ctx.env["CXXSHLINK"] = ["link.exe"]
    ctx.env["CXXSHLINKFLAGS"] = []
    ctx.env["CXXSHLINK_TGT_F"] = ["/out:"]
    ctx.env["CXXSHLINK_SRC_F"] = []

    ctx.env["CC_OBJECT_FMT"] = "%s.obj"
    ctx.env["CXX_OBJECT_FMT"] = "%s.obj"
    ctx.env["PROGRAM_FMT"] = "%s.exe"

    init()

def init():
    # We temporarily use distutils to initialize
    # environment so that we can use msvc. This will be
    # removed as soon as we have a proper msvc tool which
    # knows how to initialize itself
    compiler = distutils.ccompiler.new_compiler(
            compiler="msvc")
    compiler.initialize()
    for task_class in ["cc", "cxx", "pycc", "pycxx"]:
        klass = yaku.task.task_factory(task_class)
        saved = klass.exec_command
        klass.exec_command = _exec_command_factory(saved)

def detect(ctx):
    from distutils.ccompiler import new_compiler
    try:
        cc = new_compiler(compiler="msvc")
        cc.initialize()
        return True
    except Exception, e:
        return False
