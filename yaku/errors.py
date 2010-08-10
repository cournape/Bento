class YakuError(Exception):
    pass

class TaskRunFailure(YakuError):
    def __init__(self, cmd, explain=None):
        self.cmd = cmd
        self.explain = explain

    def __str__(self):
        return "cmd %s failed: \n\n%s" % (" ".join(self.cmd), self.explain)

class ToolNotFound(YakuError):
    pass
