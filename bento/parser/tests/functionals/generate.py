import sys

import os.path as op

from pprint \
    import \
        pprint

from bento.parser.nodes import ast_walk
from bento.parser.visitor import Dispatcher
from bento.parser.parser import parse

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        data = open(arg).read()
    else:
        raise ValueError("Usage: generate foo.info")

    base, _ = op.splitext(op.basename(arg))
    base = "data_" + base
    py_module  = op.join(op.dirname(arg), base + ".py")
    p = parse(data)
    dispatcher = Dispatcher()
    res = ast_walk(p, dispatcher)
    with open(py_module, "w") as fid:
        fid.write("ref = ")
        pprint(res, fid)
