import os
import sys

from bento.compat.api.moves \
    import \
        unittest
from bento.parser.nodes \
    import \
        ast_walk
from bento.parser.visitor \
    import \
        Dispatcher
from bento.parser.parser \
    import \
        parse as _parse

def parse(data):
    p = _parse(data)
    dispatcher = Dispatcher()
    return ast_walk(p, dispatcher)

class TestPackages(unittest.TestCase):
    def _test_functional(self, root):
        info = os.path.join(os.path.dirname(__file__), root + ".info")

        saved_path = sys.path[:]
        try:
            sys.path.insert(0, os.path.dirname(__file__))
            m = __import__("data_%s" % root)

            tested = parse(open(info).read())
            self.assertEqual(tested, m.ref, "divergence for %s" % info)
        finally:
            sys.path = saved_path

    def test_sphinx(self):
        self._test_functional("sphinx")

    def test_jinja2(self):
        self._test_functional("jinja2")

    def test_distribute(self):
        self._test_functional("distribute")
