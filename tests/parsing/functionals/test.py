import os

from unittest \
    import \
        TestCase
from nose.tools \
    import \
        assert_equal, assert_raises

from toydist.core.parser.nodes \
    import \
        ast_walk
from toydist.core.parser.visitor \
    import \
        Dispatcher
from toydist.core.parser.parser \
    import \
        parse as _parse

def parse(data):
    p = _parse(data)
    dispatcher = Dispatcher()
    return ast_walk(p, dispatcher)

def _test_functional(root):
    py_module = root
    info = os.path.join(os.path.dirname(__file__), root + ".info")
    exec("from %s import ref" % py_module)

    tested = parse(open(info).read())
    assert_equal(tested, ref, "divergence for %s" % info)

def test_sphinx():
    _test_functional("sphinx")

def test_jinja2():
    _test_functional("jinja2")
