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

    def test_meta_url(self):
        data = "Url: http://example.com"
        expected = """\
Node(type='stmt_list'):
    Node(type='url', value='http://example.com')\
"""

        self._test(data, expected)

    def test_meta_summary(self):
        data = "Summary: a few words of description."
        expected = """\
Node(type='stmt_list'):
    Node(type='summary', value=[Node('literal'), Node('literal'), """ \
        """Node('literal'), Node('literal'), Node('literal'), """ \
        """Node('literal'), Node('literal'), Node('literal'), """ \
        """Node('literal'), Node('literal'), Node('literal')])"""

        self._test(data, expected)

    def test_meta_author(self):
        data = "Author: John Doe"
        expected = """\
Node(type='stmt_list'):
    Node(type='author', value=' John Doe')"""

        self._test(data, expected)

    def test_meta_author_email(self):
        data = "AuthorEmail: john@doe.com"
        expected = """\
Node(type='stmt_list'):
    Node(type='author_email', value='john@doe.com')"""

        self._test(data, expected)

    def test_meta_maintainer_email(self):
        data = "MaintainerEmail: john@doe.com"
        expected = """\
Node(type='stmt_list'):
    Node(type='maintainer_email', value='john@doe.com')"""

        self._test(data, expected)

    def test_meta_maintainer(self):
        data = "Maintainer: John Doe"
        expected = """\
Node(type='stmt_list'):
    Node(type='maintainer', value=' John Doe')"""

        self._test(data, expected)

    def test_meta_license(self):
        data = "License: BSD"
        expected = """\
Node(type='stmt_list'):
    Node(type='license', value='BSD')"""

        self._test(data, expected)

    def test_meta_version(self):
        data = "Version: 1.0"
        expected = """\
Node(type='stmt_list'):
    Node(type='version'):
        Node(type='num_part'):
            Node(type='int', value=1)
            Node(type='int', value=0)\
"""

        self._test(data, expected)

    def test_meta_platforms(self):
        data = "Platforms: any"
        expected = """\
Node(type='stmt_list'):
    Node(type='platforms', value='any')"""

        self._test(data, expected)

