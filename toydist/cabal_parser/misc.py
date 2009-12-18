import re

_R_MODULE = re.compile(r"\w+(\.\w+)*$")

_ERR_MSG = "main section should be of the form module:function_name"

def parse_executable(s):
    if not ":" in s:
        if not _R_MODULE.match(s):
            raise ValueError(_ERR_MSG)
        return s, None
    module, func = s.split(":", 1)
    if not _R_MODULE.match(module):
        raise ValueError(_ERR_MSG)
    return module, func

def executable_meta_string(module=None, function=None):
    ret = []
    if module:
        ret.append("%s:" % module)
    if function:
        ret.append(function)
    return "".join(ret)
