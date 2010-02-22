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

def _empty_description():
    d = {"libraries": {}, "paths": {}}
    return d

def _empty_library():
    d = {"name": "default", "modules": [], "packages": [], "extensions": []}
    return d

class TestSimpleMeta(unittest.TestCase):
    def test_name(self):
        data = """\
Name: foo
"""
        ref = _empty_description()
        ref["name"] = "foo"

        assert_equal(parse_and_analyse(data), ref)

class TestDescription(unittest.TestCase):
    def test_simple_single_line(self):
        data = "Description: some simple description"

        ref = _empty_description()
        ref["description"] = " some simple description"
        assert_equal(parse_and_analyse(data), ref)

    def test_simple_indented_block(self):
        data = """\
Description:
    some simple description
    on multiple
    lines.
"""

        ref = _empty_description()
        ref["description"] = "some simple description\non multiple\nlines."
        assert_equal(parse_and_analyse(data), ref)

    def test_simple_indented_block2(self):
        data = """\
Description: some simple description
    on multiple
    lines.
"""

        ref = _empty_description()
        ref["description"] = " some simple description\non multiple\nlines."
        assert_equal(parse_and_analyse(data), ref)

    def test_nested_indented_block3(self):
        data = """\
Description: some
    simple
        description
            on
    
    multiple

    lines.
"""

        ref = _empty_description()
        ref["description"] = """ some
simple
    description
        on

multiple

lines.\
"""
        assert_equal(parse_and_analyse(data), ref)

class TestLibrary(unittest.TestCase):
    def test_modules(self):
        data = """\
Library:
    Modules: foo.py
"""

        descr = _empty_description()
        library = _empty_library()
        library["modules"] = ["foo.py"]
        descr["libraries"]["default"] = library

        assert_equal(parse_and_analyse(data), descr)
