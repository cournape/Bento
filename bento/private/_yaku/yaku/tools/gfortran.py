import yaku.utils

def setup(ctx):
    env = ctx.env

    ctx.env.update(
       {"F77": ["gfortran"],
        "F77_LINK": ["gfortran"],
        "F77FLAGS": ["-W", "-g"],
        "F77_TGT_F": ["-o"],
        "F77_SRC_F": ["-c"],
        "F77_LINKFLAGS": [],
        "F77_LINK_TGT_F": ["-o"],
        "F77_LINK_SRC_F": [],
        "F77_OBJECT_FMT": "%s.o",
        "F77_PROGRAM_FMT": "%s"})

def detect(ctx):
    if yaku.utils.find_program("gfortran") is None:
        return False
    else:
        return True
