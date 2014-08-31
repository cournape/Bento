import yaku.utils

def setup(ctx):
    env = ctx.env

    ctx.env["STLINK"] = ["ar"]
    ctx.env["STLINK_TGT_F"] = []
    ctx.env["STLINK_SRC_F"] = []
    ctx.env["STLINKFLAGS"] = ["rcs"]
    ctx.env["STATICLIB_FMT"] = "lib%s.a"

def detect(ctx):
    if yaku.utils.find_program("ar") is None:
        return False
    else:
        return True
