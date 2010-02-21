from cStringIO \
    import \
        StringIO

from unittest \
    import \
        TestCase
from nose.tools \
    import \
        assert_equal, assert_raises

import ply

from toydist.core.parser.nodes \
    import \
        Node, ast_pprint
from toydist.core.parser.parser \
    import \
        parse, Parser

class TestGrammar(TestCase):
    def _test(self, data, expected):
        s = StringIO()

        p = parse(data)
        ast_pprint(p, string=s)

        assert_equal(s.getvalue(), expected)

    def test_meta_name(self):
        data = "Name: yo"
        expected = """\
Node(type='stmt_list'):
    Node(type='name', value='yo')\
"""

        self._test(data, expected)
