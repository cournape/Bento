import os
import sys

from unittest \
    import \
        TestCase
from nose.tools \
    import \
        assert_equal, assert_raises

from bento.core.parser.nodes \
    import \
        ast_walk
from bento.core.parser.visitor \
    import \
        Dispatcher
from bento.core.parser.parser \
    import \
        parse as _parse

def parse(data):
    p = _parse(data)
    dispatcher = Dispatcher()
    return ast_walk(p, dispatcher)

def _test_functional(root):
    py_module = root
    info = os.path.join(os.path.dirname(__file__), root + ".info")

    saved_path = sys.path[:]
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        m = __import__("data_%s" % root)

        tested = parse(open(info).read())
        assert_equal(tested, m.ref, "divergence for %s" % info)
    finally:
        sys.path = saved_path

def test_sphinx():
    _test_functional("sphinx")

def test_jinja2():
    _test_functional("jinja2")
