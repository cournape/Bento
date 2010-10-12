import yaku.utils
import yaku.task

def setup(ctx):
    env = ctx.env

    ctx.env["STLINK"] = ["lib.exe"]
    ctx.env["STLINK_TGT_F"] = ["/OUT:"]
    ctx.env["STLINK_SRC_F"] = []
    ctx.env["STLINKFLAGS"] = ["/nologo"]
    ctx.env["STATICLIB_FMT"] = "%s.lib"

    # XXX: hack
    saved = yaku.task.Task.exec_command
    def msvc_exec_command(self, cmd, cwd):
        new_cmd = []
        carry = ""
        for c in cmd:
            if c in ["/OUT:"]:
                carry = c
            else:
                c = carry + c
                carry = ""
                new_cmd.append(c)
        saved(self, new_cmd, cwd)
    yaku.task.Task.exec_command = msvc_exec_command

def detect(ctx):
    if yaku.utils.find_program("lib.exe") is None:
        return False
    else:
        return True
