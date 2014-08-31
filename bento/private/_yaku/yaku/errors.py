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
        ret = "Command failed. Error was: \n\t%s\ncommand line was\n\t%r" % (self.explain.rstrip(),
                                                                          " ".join(self.cmd))
        if sys.version_info < (3,):
            return ret.encode("utf-8")
        else:
            return ret

class ConfigurationFailure(YakuError):
    pass

class UnknownTask(YakuError):
    pass

class ToolNotFound(YakuError):
    pass
