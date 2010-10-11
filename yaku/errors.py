import sys
if sys.version_info >= (3,):
    import builtins
    if not hasattr(builtins, "WindowsError"):
        class WindowsError(Exception):
            pass
    else:
	WindowsError = builtins.WindowsError
else:
    import __builtin__
    if not hasattr(__builtin__, "WindowsError"):
        class WindowsError(Exception):
            pass
    else:
	WindowsError = __builtin__.WindowsError

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
