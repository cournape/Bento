import sys

from pprint \
    import \
        pprint

from toydist.core.parser.nodes import ast_walk
from toydist.core.parser.visitor import Dispatcher
from toydist.core.parser.parser import parse

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        data = open(arg).read()
    else:
        raise ValueError("Usage: generate foo.info")

    base, ext = arg.split(".")
    py_module  = base + ".py"
    p = parse(data)
    dispatcher = Dispatcher()
    res = ast_walk(p, dispatcher)
    with open(py_module, "w") as fid:
        fid.write("ref = ")
        pprint(res, fid)
