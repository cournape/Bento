def detect(ctx):
    env = ctx.env

    ctx.env.update(
       {"F77": ["gfortran"],
        "F77FLAGS": ["-W", "-g"]})
