import sys
import copy

from yaku._config \
    import \
        TOOLDIRS

def import_tools(tool_list, tooldirs=None):
    old_sys = sys.path[:]
    if tooldirs is not None:
        sys.path = tooldirs + TOOLDIRS + sys.path
    else:
        sys.path = TOOLDIRS + sys.path

    try:
        ret = {}
        for t in tool_list:
            ret[t] = __import__(t)
        return ret
    finally:
        sys.path = old_sys

class Builder(object):
    def __init__(self, ctx):
        self.configured = False
        self.ctx = ctx
        self.env = copy.deepcopy(ctx.env)

    def configure(self):
        pass
