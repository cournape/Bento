import unittest
import sys

from nose.tools \
    import \
        assert_equal

from bento.core.parser.parser \
    import \
        parse
from bento.core.parser.nodes \
    import \
        ast_walk, Node
from bento.core.parser.visitor \
    import \
        Dispatcher

def parse_and_analyse(data):
    p = parse(data)
    dispatcher = Dispatcher()
    res = ast_walk(p, dispatcher)

    return res

def _empty_description():
    d = {"libraries": {}, "path_options": {}, "flag_options": {},
         "data_files": {}, "extra_sources": [], "executables": {}}
    return d

def _empty_library():
    d = {"name": "default", "py_modules": [], "packages": [], "extensions": {},
         "build_requires": [], "install_requires": [], "compiled_libraries": {}}
    return d

class TestSimpleMeta(unittest.TestCase):
    def test_empty(self):
        data = ""
        assert_equal(parse_and_analyse(data), {})

    def test_name(self):
        data = """\
Name: foo
"""
        ref = {"name": "foo"}
        assert_equal(parse_and_analyse(data), ref)

    def test_summary(self):
        data = """\
Summary: a few words.
"""
        ref = {"summary": "a few words."}
        assert_equal(parse_and_analyse(data), ref)

    def test_author(self):
        data = """\
Author: John Doe
"""
        ref = {"author": "John Doe"}

        assert_equal(parse_and_analyse(data), ref)

class TestDescription(unittest.TestCase):
    def test_simple_single_line(self):
        data = "Description: some simple description"

        ref = {"description": "some simple description"}
        assert_equal(parse_and_analyse(data), ref)

    def test_simple_indented_block(self):
        data = """\
Description:
    some simple description
    on multiple
    lines.
"""
        ref = {"description": "some simple description\non multiple\nlines."}
        assert_equal(parse_and_analyse(data), ref)

    def test_simple_indented_block2(self):
        data = """\
Description: some simple description
    on multiple
    lines.
"""
        ref = {"description": "some simple description\non multiple\nlines."}
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

        ref = {"description": """some
simple
    description
        on

multiple

lines.\
"""}
        assert_equal(parse_and_analyse(data), ref)

class TestLibrary(unittest.TestCase):
    def test_empty(self):
        data = """\
Library:
"""

        ref = {"libraries": {"default": {"name": "default"}}}
        assert_equal(parse_and_analyse(data), ref)

    def test_modules(self):
        data = """\
Library:
    Modules: foo.py
"""

        ref = {"libraries": {"default": {"name": "default", "py_modules": ["foo.py"]}}}
        assert_equal(parse_and_analyse(data), ref)

    def test_simple_extension(self):
        data = """\
Library:
    Extension: _foo
        Sources: foo.c
"""
        extension = {"name": "_foo", "sources": ["foo.c"]}
        ref = {"libraries": {"default": {"name": "default",
                                         "extensions": {"_foo": extension}}}}
        assert_equal(parse_and_analyse(data), ref)

    def test_build_requires(self):
        data = """\
Library:
    BuildRequires: foo
"""
        ref = {"libraries": {"default": {"name": "default",
                                         "build_requires": ["foo"]}}}
        assert_equal(parse_and_analyse(data), ref)

    def test_install_requires(self):
        data = """\
Library:
    InstallRequires: foo
"""
        ref = {"libraries": {"default": {"name": "default",
                                         "install_requires": ["foo"]}}}
        assert_equal(parse_and_analyse(data), ref)

class TestPath(unittest.TestCase):
    def test_simple(self):
        data = """\
Path: manpath
    Description: man path
    Default: /usr/share/man
"""

        descr = {"path_options": {"manpath": {"name": "manpath",
                                              "default": "/usr/share/man",
                                              "description": "man path"}}}
        assert_equal(parse_and_analyse(data), descr)

class TestDataFiles(unittest.TestCase):
    def test_simple(self):
        data = """\
DataFiles: man1doc
    TargetDir: /usr/share/man/man1
    SourceDir: doc/man1
    Files: foo.1
"""

        ref = {"data_files": {"man1doc": {"name": "man1doc",
                                          "target_dir": "/usr/share/man/man1",
                                          "source_dir": "doc/man1",
                                          "files": ["foo.1"]}}}
        assert_equal(parse_and_analyse(data), ref)

class TestFlag(unittest.TestCase):
    def test_simple(self):
        data = """\
Flag: debug
    Description: debug flag
    Default: false
"""
        ref = {"flag_options": {"debug": {"name": "debug",
                                          "default": "false",
                                          "description": "debug flag"}}}
        assert_equal(parse_and_analyse(data), ref)

class TestConditional(unittest.TestCase):
    def test_literal(self):
        data = """\
Library:
    if true:
        Modules: foo.py, bar.py
    else:
        Modules:  fubar.py
"""

        ref = {"libraries": {"default": {"name": "default",
                                         "py_modules": ["foo.py", "bar.py"]}}}
        assert_equal(parse_and_analyse(data), ref)

        data = """\
Library:
    if false:
        Modules: foo.py, bar.py
    else:
        Modules:  fubar.py
"""
        ref["libraries"]["default"]["py_modules"] = ["fubar.py"]

        assert_equal(parse_and_analyse(data), ref)

    def test_os(self):
        data = """\
Library:
    if os(%s):
        Modules: foo.py, bar.py
    else:
        Modules:  fubar.py
""" % sys.platform

        ref = {"libraries": {"default": {"name": "default",
                                         "py_modules": ["foo.py", "bar.py"]}}}
        assert_equal(parse_and_analyse(data), ref)

    def test_flag(self):
        data = """\
Flag: debug
    Default: true

Library:
    if flag(debug):
        Modules: foo.py, bar.py
    else:
        Modules:  fubar.py
"""

        ref = {"libraries": {"default": {"name": "default",
                                         "py_modules": ["foo.py", "bar.py"]}},
               "flag_options": {"debug": {"default": "true",
                                          "name": "debug"}}}
        assert_equal(parse_and_analyse(data), ref)

        data = """\
Flag: debug
    Default: false

Library:
    if flag(debug):
        Modules: foo.py, bar.py
    else:
        Modules:  fubar.py
"""

        ref["libraries"]["default"]["py_modules"] = ["fubar.py"]
        ref["flag_options"]["debug"] = {"default": "false", "name": "debug"}

        assert_equal(parse_and_analyse(data), ref)

class TestExecutable(unittest.TestCase):
    def test_modules(self):
        data = """\
Executable: foo
    Module: foo.bar
    Function: main
"""
        ref = {"executables": {"foo": {"module": "foo.bar",
                                       "function": "main",
                                       "name": "foo"}}}
        assert_equal(parse_and_analyse(data), ref)
