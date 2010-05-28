import sys

from pprint \
    import \
        pprint

from bento.core.parser.nodes import ast_walk
from bento.core.parser.visitor import Dispatcher
from bento.core.parser.parser import parse

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
