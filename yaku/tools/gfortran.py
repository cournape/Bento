import yaku.utils

def setup(ctx):
    env = ctx.env

    ctx.env.update(
       {"F77": ["gfortran"],
        "F77FLAGS": ["-W", "-g"],
        "F77_TGT_F": ["-o"],
        "F77_SRC_F": ["-c"]})

def detect(ctx):
    if yaku.utils.find_program("gcc") is None:
        return False
    else:
        return True
