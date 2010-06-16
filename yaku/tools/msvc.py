import yaku.task

def detect(ctx):
    env = ctx.env

    ctx.env["CC"] = ["cl.exe"]
    ctx.env["CC_TGT_F"] = ["/c", "/Fo"]
    ctx.env["CC_SRC_F"] = []
    ctx.env["CFLAGS"] = []
    ctx.env["CPPPATH"] = []
    ctx.env["CPPPATH_FMT"] = "/I%s"
    ctx.env["LINK"] = ["link.exe"]
    ctx.env["LINKFLAGS"] = []
    ctx.env["LIBS"] = []
    ctx.env["LIB_FMT"] = "%s.lib"
    ctx.env["LIBDIR"] = []
    ctx.env["LIBDIR_FMT"] = "/L%s"

    ctx.env["PROGRAM_FMT"] = "%s.exe"
    ctx.env["CC_OBJECT_FMT"] = "%s.obj"

    # XXX: hack
    saved = yaku.task.Task.exec_command
    def msvc_exec_command(self, cmd, cwd):
        new_cmd = []
        carry = ""
        for c in cmd:
            if c in ["/Fo", "/out:"]:
                carry = c
            else:
                c = carry + c
                carry = ""
                new_cmd.append(c)
        saved(self, new_cmd, cwd)
    yaku.task.Task.exec_command = msvc_exec_command
