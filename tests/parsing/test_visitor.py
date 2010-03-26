import unittest
import sys

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
    d = {"libraries": {}, "path_options": {}, "flag_options": {},
         "data_files": {}, "extra_sources": [], "executables": {}}
    return d

def _empty_library():
    d = {"name": "default", "py_modules": [], "packages": [], "extensions": {},
         "build_requires": [], "install_requires": []}
    return d

class TestSimpleMeta(unittest.TestCase):
    def test_name(self):
        data = """\
Name: foo
"""
        ref = _empty_description()
        ref["name"] = "foo"

        assert_equal(parse_and_analyse(data), ref)

    def test_summary(self):
        data = """\
Summary: a few words.
"""
        ref = _empty_description()
        ref["summary"] = "a few words."

        assert_equal(parse_and_analyse(data), ref)

    def test_author(self):
        data = """\
Author: John Doe
"""
        ref = _empty_description()
        ref["author"] = "John Doe"

        assert_equal(parse_and_analyse(data), ref)

class TestDescription(unittest.TestCase):
    def test_simple_single_line(self):
        data = "Description: some simple description"

        ref = _empty_description()
        ref["description"] = "some simple description"
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
        ref["description"] = "some simple description\non multiple\nlines."
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
        ref["description"] = """some
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
        library["py_modules"] = ["foo.py"]
        descr["libraries"]["default"] = library

        assert_equal(parse_and_analyse(data), descr)

    def test_simple_extension(self):
        data = """\
Library:
    Extension: _foo
        Sources: foo.c
"""
        descr = _empty_description()
        library = _empty_library()
        library["extensions"]["_foo"] = {"name": "_foo", "sources": ["foo.c"]}
        descr["libraries"]["default"] = library

        assert_equal(parse_and_analyse(data), descr)

    def test_build_requires(self):
        data = """\
Library:
    BuildRequires: foo
"""
        descr = _empty_description()
        library = _empty_library()
        library["build_requires"] = ["foo"]
        descr["libraries"]["default"] = library

        assert_equal(parse_and_analyse(data), descr)

    def test_install_requires(self):
        data = """\
Library:
    InstallRequires: foo
"""
        descr = _empty_description()
        library = _empty_library()
        library["install_requires"] = ["foo"]
        descr["libraries"]["default"] = library

        assert_equal(parse_and_analyse(data), descr)

class TestPath(unittest.TestCase):
    def test_simple(self):
        data = """\
Path: manpath
    Description: man path
    Default: /usr/share/man
"""

        descr = _empty_description()
        descr["path_options"]["manpath"] = {
                "name": "manpath",
                "default": "/usr/share/man",
                "description": "man path",
                }

        assert_equal(parse_and_analyse(data), descr)

class TestDataFiles(unittest.TestCase):
    def test_simple(self):
        data = """\
DataFiles: man1doc
    TargetDir: /usr/share/man/man1
    SourceDir: doc/man1
    Files: foo.1
"""

        descr = _empty_description()
        descr["data_files"]["man1doc"] = {
                "name": "man1doc",
                "target_dir": "/usr/share/man/man1",
                "source_dir": "doc/man1",
                "files": ["foo.1"],
                }

        assert_equal(parse_and_analyse(data), descr)

class TestFlag(unittest.TestCase):
    def test_simple(self):
        data = """\
Flag: debug
    Description: debug flag
    Default: false
"""

        descr = _empty_description()
        descr["flag_options"]["debug"] = {
                "name": "debug",
                "default": "false",
                "description": "debug flag",
                }

        assert_equal(parse_and_analyse(data), descr)

class TestConditional(unittest.TestCase):
    def test_literal(self):
        data = """\
Library:
    if true:
        Modules: foo.py, bar.py
    else:
        Modules:  fubar.py
"""

        descr = _empty_description()
        descr["libraries"]["default"] = _empty_library()
        descr["libraries"]["default"]["py_modules"] = ["foo.py", "bar.py"]

        assert_equal(parse_and_analyse(data), descr)

        data = """\
Library:
    if false:
        Modules: foo.py, bar.py
    else:
        Modules:  fubar.py
"""
        descr["libraries"]["default"]["py_modules"] = ["fubar.py"]

        assert_equal(parse_and_analyse(data), descr)

    def test_os(self):
        data = """\
Library:
    if os(%s):
        Modules: foo.py, bar.py
    else:
        Modules:  fubar.py
""" % sys.platform

        descr = _empty_description()
        descr["libraries"]["default"] = _empty_library()
        descr["libraries"]["default"]["py_modules"] = ["foo.py", "bar.py"]

        assert_equal(parse_and_analyse(data), descr)

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

        descr = _empty_description()
        descr["libraries"]["default"] = _empty_library()
        descr["libraries"]["default"]["py_modules"] = ["foo.py", "bar.py"]
        descr["flag_options"]["debug"] = {"default": "true", "name": "debug"}

        assert_equal(parse_and_analyse(data), descr)

        data = """\
Flag: debug
    Default: false

Library:
    if flag(debug):
        Modules: foo.py, bar.py
    else:
        Modules:  fubar.py
"""

        descr = _empty_description()
        descr["libraries"]["default"] = _empty_library()
        descr["libraries"]["default"]["py_modules"] = ["fubar.py"]
        descr["flag_options"]["debug"] = {"default": "false", "name": "debug"}

        assert_equal(parse_and_analyse(data), descr)

class TestExecutable(unittest.TestCase):
    def test_modules(self):
        data = """\
Executable: foo
    Module: foo.bar
    Function: main
"""

        descr = _empty_description()
        executable = {"name": "foo", "module": "foo.bar", "function": "main"}
        descr["executables"]["foo"] = executable

        assert_equal(parse_and_analyse(data), descr)

