class YakuError(Exception):
    pass

class TaskRunFailure(YakuError):
    pass

class ToolNotFound(YakuError):
    pass
