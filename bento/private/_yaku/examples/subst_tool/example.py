import subprocess

from yaku.context \
    import \
        get_bld, get_cfg
from yaku.scheduler \
    import \
        run_tasks

def git_revision():
    p = subprocess.Popen("git rev-parse --short HEAD", stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, shell=True)
    o, _ = p.communicate()
    if p.returncode:
        raise ValueError("Failed to execute git rev-parse")
    else:
        return o

def configure(ctx):
    tools = ctx.use_tools(["template"])

def build(ctx):
    builder = ctx.builders["template"]
    vars = {}
    vars["HEAD"] = git_revision()
    builder.render(["foo.ini.in"], vars)

if __name__ == "__main__":
    ctx = get_cfg()
    configure(ctx)
    ctx.store()

    ctx = get_bld()
    build(ctx)
    run_tasks(ctx)
    ctx.store()
