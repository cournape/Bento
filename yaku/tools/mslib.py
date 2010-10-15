import yaku.utils
import yaku.task
from yaku.tools.msvc \
    import \
        _exec_command_factory

def setup(ctx):
    env = ctx.env

    ctx.env["STLINK"] = ["lib.exe"]
    ctx.env["STLINK_TGT_F"] = ["/OUT:"]
    ctx.env["STLINK_SRC_F"] = []
    ctx.env["STLINKFLAGS"] = ["/nologo"]
    ctx.env["STATICLIB_FMT"] = "%s.lib"

    init()

def init():
    for task_class in ["cc_link", "cxx_link", "ccprogram", "cxxprogram", "pylink"]:
        klass = yaku.task.task_factory(task_class)
        saved = klass.exec_command
        klass.exec_command = _exec_command_factory(saved)

def detect(ctx):
    if yaku.utils.find_program("lib.exe") is None:
        return False
    else:
        return True
