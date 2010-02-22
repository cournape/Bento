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

    def test_meta_classifiers_single_line(self):
        data = "Classifiers: yo"
        expected = """\
Node(type='stmt_list'):
    Node(type='classifiers'):
        Node(type='classifier', value=' yo')\
"""

        self._test(data, expected)

    def test_meta_classifiers_indent_only(self):
        data = """\
Classifiers:
    yo1
    yo2\
"""
        expected = """\
Node(type='stmt_list'):
    Node(type='classifiers'):
        Node(type='classifiers_list'):
            Node(type='classifier', value='yo1')
            Node(type='classifier', value='yo2')\
"""

        self._test(data, expected)

    def test_meta_classifiers_full(self):
        data = """\
Classifiers: yo1
    yo2\
"""
        expected = """\
Node(type='stmt_list'):
    Node(type='classifiers'):
        Node(type='classifier', value=' yo1')
        Node(type='classifiers_list'):
            Node(type='classifier', value='yo2')\
"""

        self._test(data, expected)

    def test_meta_stmts(self):
        data = """\
Name: yo
Summary: yeah\
"""
        expected = """\
Node(type='stmt_list'):
    Node(type='name', value='yo')
    Node(type='summary', value=[Node('literal'), Node('literal')])\
"""

        self._test(data, expected)

    def test_empty(self):
        data = ""
        expected = "None"

        self._test(data, expected)

    def test_newline(self):
        data = "\n"
        expected = "None"

        self._test(data, expected)

    def test_description_single_line(self):
        data = "Description: some words."
        expected = """\
Node(type='stmt_list'):
    Node(type='description'):
        Node(type='single_line', value=[Node('literal'), """ \
        """Node('literal'), Node('literal'), Node('literal'), """\
        """Node('literal')])"""

        self._test(data, expected)

    def test_description_simple_indent(self):
        data = """\
Description:
    some words."""
        expected = """\
Node(type='stmt_list'):
    Node(type='description', value=[Node('multi_literal'), Node('multi_literal'), """ \
        """Node('multi_literal'), Node('multi_literal')])"""

        self._test(data, expected)

    def test_description_complex_indent(self):
        data = """\
Description:
    some
        indented
            words
    ."""

        expected = """\
Node(type='stmt_list'):
    Node(type='description', value=[Node('multi_literal'), Node('newline'), """ \
        """Node('indent'), """ \
        """Node('multi_literal'), """ \
        """Node('newline'), Node('indent'), """ \
        """Node('multi_literal'), Node('newline'), """ \
        """Node('dedent'), Node('dedent'), """ \
        """Node('multi_literal')])"""

        self._test(data, expected)
