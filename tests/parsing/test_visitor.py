import unittest

from nose.tools \
    import \
        assert_equal

from toydist.core.parser.parser \
    import \
        parse
from toydist.core.parser.nodes \
    import \
        ast_walk
from toydist.core.parser.visitor \
    import \
        Dispatcher

def parse_and_analyse(data):
    p = parse(data)
    dispatcher = Dispatcher()
    res = ast_walk(p, dispatcher)

    return res

class TestSimpleMeta(unittest.TestCase):
    def test_name(self):
        data = """\
Name: foo
"""

        assert_equal(parse_and_analyse(data), {"name": "foo"})

class TestDescription(unittest.TestCase):
    def test_simple_single_line(self):
        data = "Description: some simple description"

        assert_equal(parse_and_analyse(data),
                     {"description": " some simple description"})

    def test_simple_indented_block(self):
        data = """\
Description:
    some simple description
    on multiple
    lines.
"""

        ref = {
            "description": "some simple description\non multiple\nlines."
        }
        assert_equal(parse_and_analyse(data), ref)

    def test_simple_indented_block2(self):
        data = """\
Description: some simple description
    on multiple
    lines.
"""

        ref = {
            "description": " some simple description\non multiple\nlines."
        }
        assert_equal(parse_and_analyse(data), ref)

    def test_nested_indented_block(self):
        data = """\
Description: some
    simple
        description
            on
    
    multiple

    lines.
"""

        ref = {
            "description": """ some
simple
    description
        on

multiple

lines.\
"""
        }
        assert_equal(parse_and_analyse(data), ref)
