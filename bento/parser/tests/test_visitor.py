import sys
import warnings

from bento.compat.api.moves \
    import \
        unittest
from bento.parser.parser \
    import \
        parse
from bento.parser.nodes \
    import \
        ast_walk
from bento.parser.visitor \
    import \
        Dispatcher

def parse_and_analyse(data):
    p = parse(data)
    dispatcher = Dispatcher()
    res = ast_walk(p, dispatcher)

    return res

def _empty_description():
    d = {"libraries": {}, "path_options": {}, "flag_options": {},
         "data_files": {}, "extra_source_files": [], "executables": {},
         "hook_files": []}
    return d

def _empty_library():
    d = {"name": "default", "py_modules": [], "packages": [], "extensions": {},
         "build_requires": [], "install_requires": [], "compiled_libraries": {},
         "sub_directory": None}
    return d

class TestSimpleMeta(unittest.TestCase):
    def setUp(self):
        self.ref = _empty_description()

    def test_empty(self):
        data = ""
        self.assertEqual(parse_and_analyse(data), self.ref)

    def test_name(self):
        data = """\
Name: foo
"""
        self.ref["name"] = "foo"
        self.assertEqual(parse_and_analyse(data), self.ref)

    def test_summary(self):
        data = """\
Summary: a few words.
"""
        self.ref.update({"summary": "a few words."})
        self.assertEqual(parse_and_analyse(data), self.ref)

    def test_author(self):
        data = """\
Author: John Doe
"""
        self.ref.update({"author": "John Doe"})
        self.assertEqual(parse_and_analyse(data), self.ref)

    def test_maintainer(self):
        data = """\
Maintainer: John Doe
"""
        self.assertEqual(parse_and_analyse(data)["maintainer"], "John Doe")

    def test_use_backends(self):
        data = """\
UseBackends: foo
"""
        self.assertEqual(parse_and_analyse(data)["use_backends"], ["foo"])

        data = """\
UseBackends: foo, bar
"""
        self.assertEqual(parse_and_analyse(data)["use_backends"], ["foo", "bar"])

    def test_hook(self):
        data = """\
HookFile: bscript
"""
        self.assertEqual(parse_and_analyse(data)["hook_files"], ["bscript"])

        data = """\
HookFile: bscript, bscript2
"""
        self.assertEqual(parse_and_analyse(data)["hook_files"], ["bscript", "bscript2"])

class TestDescription(unittest.TestCase):
    def setUp(self):
        self.ref = _empty_description()

    def test_simple_single_line(self):
        data = "Description: some simple description"

        self.ref.update({"description": "some simple description"})
        self.assertEqual(parse_and_analyse(data), self.ref)

    def test_simple_indented_block(self):
        data = """\
Description:
    some simple description
    on multiple
    lines.
"""
        self.ref["description"] = "some simple description\non multiple\nlines."
        self.assertEqual(parse_and_analyse(data), self.ref)

    def test_simple_indented_block2(self):
        data = """\
Description: some simple description
    on multiple
    lines.
"""
        self.ref["description"] = "some simple description\non multiple\nlines."
        self.assertEqual(parse_and_analyse(data), self.ref)

    def test_nested_indented_block3(self):
        data = """\
Description: some
    simple
        description
            on
    
    multiple

    lines.
"""

        self.ref["description"] = """some
simple
    description
        on

multiple

lines.\
"""
        self.assertEqual(parse_and_analyse(data), self.ref)

    def test_nested_indented_block2(self):
        last_indent = " " * 4
        data = """\
Description: some
    simple
        description
            on
%s
Name: foo
""" % last_indent

        self.ref["name"] = "foo"
        self.ref["description"] = """some
simple
    description
        on
"""
        self.assertEqual(parse_and_analyse(data), self.ref)

    def test_description_from_file(self):
        data = """\
DescriptionFromFile: foo.rst
"""
        ret = parse_and_analyse(data)
        self.assertEqual(ret["description_from_file"], "foo.rst")

    def test_meta_template_file(self):
        s = warnings.filters[:]
        warnings.filterwarnings("ignore")
        try:
            data = """\
MetaTemplateFile: foo.py.in
"""
            ret = parse_and_analyse(data)
            self.assertEqual(ret["meta_template_files"], ["foo.py.in"])
        finally:
            warnings.filters = s

    def test_meta_template_files(self):
        data = """\
MetaTemplateFiles: foo.py.in
"""
        ret = parse_and_analyse(data)
        self.assertEqual(ret["meta_template_files"], ["foo.py.in"])

class TestLibrary(unittest.TestCase):
    def setUp(self):
        self.ref = _empty_description()
        self.ref["libraries"]["default"] = _empty_library()

    def test_empty(self):
        data = """\
Library:
"""

        #self.ref["libraries"] = {"default": {"name": "default"}}
        self.assertEqual(parse_and_analyse(data), self.ref)

    def test_sub_directory(self):
        self.maxDiff = None
        data = """\
Library:
    SubDirectory: lib
"""

        self.ref["libraries"]["default"]["sub_directory"] = "lib"
        self.assertEqual(parse_and_analyse(data), self.ref)

    def test_modules(self):
        data = """\
Library:
    Modules: foo.py
"""

        self.ref["libraries"]["default"].update({"py_modules": ["foo.py"]})
        self.assertEqual(parse_and_analyse(data), self.ref)

    def test_simple_extension(self):
        data = """\
Library:
    Extension: _foo
        Sources: foo.c
"""
        extension = {"name": "_foo", "sources": ["foo.c"]}
        self.ref["libraries"]["default"].update({"extensions": {"_foo": extension}})
        self.assertEqual(parse_and_analyse(data), self.ref)

    def test_extension_include_dirs(self):
        data = """\
Library:
    Extension: _foo
        Sources: foo.c
        IncludeDirs: foo
"""
        r_extension = {"name": "_foo", "sources": ["foo.c"], "include_dirs": ["foo"]}
        extension = parse_and_analyse(data)["libraries"]["default"]["extensions"]["_foo"]
        self.assertEqual(extension, r_extension)

    def test_double_sources_extension(self):
        data = """\
Library:
    Extension: _foo
        Sources: foo.c
        Sources: bar.c
"""
        self.assertRaises(ValueError, lambda: parse_and_analyse(data))

    def test_build_requires(self):
        data = """\
Library:
    BuildRequires: foo
"""
        self.ref["libraries"]["default"].update({"build_requires": ["foo"]})
        self.assertEqual(parse_and_analyse(data), self.ref)

    def test_install_requires(self):
        data = """\
Library:
    InstallRequires: foo
"""
        self.ref["libraries"]["default"].update({"install_requires": ["foo"]})
        self.assertEqual(parse_and_analyse(data), self.ref)

    def test_compiled_library_include_dirs(self):
        data = """\
Library:
    CompiledLibrary: _foo
        Sources: foo.c
        IncludeDirs: foo
"""
        r_compiled_library = {"name": "_foo", "sources": ["foo.c"], "include_dirs": ["foo"]}
        compiled_library = parse_and_analyse(data)["libraries"]["default"]["compiled_libraries"]["_foo"]
        self.assertEqual(compiled_library, r_compiled_library)

    def test_double_sources_compiled_library(self):
        data = """\
Library:
    CompiledLibrary: _foo
        Sources: foo.c
        Sources: bar.c
"""
        self.assertRaises(ValueError, lambda: parse_and_analyse(data))

class TestPath(unittest.TestCase):
    def test_simple(self):
        data = """\
Path: manpath
    Description: man path
    Default: /usr/share/man
"""

        descr = _empty_description()
        descr["path_options"] = {"manpath": {"name": "manpath",
                                             "default": "/usr/share/man",
                                             "description": "man path"}}
        self.assertEqual(parse_and_analyse(data), descr)

    def test_multiple_path_sections(self):
        data = """\
Path: manpath
    Description: man path
    Default: /usr/share/man

Path: varpath
    Description: var path
    Default: /var
"""

        data_sections = parse_and_analyse(data)["path_options"]
        r_data_sections = {
                "manpath": {"name": "manpath", "description": "man path", "default": "/usr/share/man"},
                "varpath": {"name": "varpath", "description": "var path", "default": "/var"},
        }
        self.assertEqual(data_sections, r_data_sections)

    def test_conditional_path_section(self):
        data_template = """\
Path: manpath
    Description: man path
    if %s:
        Default: /usr/share/woman
    else:
        Default: /usr/share/man
"""

        data_sections = parse_and_analyse(data_template % "true")["path_options"]
        r_data_sections = {
                "manpath": {"name": "manpath", "description": "man path", "default": "/usr/share/woman"},
        }
        self.assertEqual(data_sections, r_data_sections)

        data_sections = parse_and_analyse(data_template % "false")["path_options"]
        r_data_sections = {
                "manpath": {"name": "manpath", "description": "man path", "default": "/usr/share/man"},
        }
        self.assertEqual(data_sections, r_data_sections)

    def test_invalid_path_section1(self):
        data = """\
Path: manpath
    Description: description
"""
        self.assertRaises(ValueError, lambda: parse_and_analyse(data))

        data = """\
Path: manpath
    Default: /foo/bar
"""
        self.assertRaises(ValueError, lambda: parse_and_analyse(data))

class TestDataFiles(unittest.TestCase):
    def test_simple(self):
        data = """\
DataFiles: man1doc
    TargetDir: /usr/share/man/man1
    SourceDir: doc/man1
    Files: foo.1
"""

        ref = _empty_description()
        ref["data_files"] = {"man1doc": {"name": "man1doc",
                                         "target_dir": "/usr/share/man/man1",
                                         "source_dir": "doc/man1",
                                         "files": ["foo.1"]}}
        self.assertEqual(parse_and_analyse(data), ref)

class TestFlag(unittest.TestCase):
    def setUp(self):
        self.ref = _empty_description()

    def test_simple(self):
        data = """\
Flag: debug
    Description: debug flag
    Default: false
"""
        self.ref["flag_options"] = {"debug": {"name": "debug",
                                              "default": "false",
                                              "description": "debug flag"}}
        self.assertEqual(parse_and_analyse(data), self.ref)

class TestConditional(unittest.TestCase):
    def setUp(self):
        self.ref = _empty_description()
        self.ref["libraries"]["default"] = _empty_library()

    def test_literal(self):
        data = """\
Library:
    if true:
        Modules: foo.py, bar.py
    else:
        Modules:  fubar.py
"""

        self.ref["libraries"]["default"].update({"py_modules": ["foo.py", "bar.py"]})
        self.assertEqual(parse_and_analyse(data), self.ref)

        data = """\
Library:
    if false:
        Modules: foo.py, bar.py
    else:
        Modules:  fubar.py
"""
        self.ref["libraries"]["default"]["py_modules"] = ["fubar.py"]

        self.assertEqual(parse_and_analyse(data), self.ref)

    def test_os(self):
        data = """\
Library:
    if os(%s):
        Modules: foo.py, bar.py
    else:
        Modules:  fubar.py
""" % sys.platform

        self.ref["libraries"]["default"].update({"py_modules": ["foo.py", "bar.py"]})
        self.assertEqual(parse_and_analyse(data), self.ref)

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

        self.ref["libraries"]["default"].update({"py_modules": ["foo.py", "bar.py"]})
        self.ref["flag_options"] = {"debug": {"default": "true",
                                              "name": "debug"}}
        self.assertEqual(parse_and_analyse(data), self.ref)

        data = """\
Flag: debug
    Default: false

Library:
    if flag(debug):
        Modules: foo.py, bar.py
    else:
        Modules:  fubar.py
"""

        self.ref["libraries"]["default"]["py_modules"] = ["fubar.py"]
        self.ref["flag_options"]["debug"] = {"default": "false", "name": "debug"}

        self.assertEqual(parse_and_analyse(data), self.ref)

    def test_not_flag(self):
        data = """\
Flag: debug
    Default: true

Library:
    if not flag(debug):
        Modules: foo.py, bar.py
    else:
        Modules:  fubar.py
"""

        self.ref["libraries"]["default"].update({"py_modules": ["fubar.py"]})
        self.ref["flag_options"] = {"debug": {"default": "true",
                                              "name": "debug"}}
        self.assertEqual(parse_and_analyse(data), self.ref)

    def test_missing_flag(self):
        data = """\
Flag: debug
    Default: true

Library:
    if flag(ddebug):
        Modules: bar.py
"""
        self.assertRaises(ValueError, lambda: parse_and_analyse(data))

        data = """\
Flag: debug
    Default: true

Library:
    if not flag(ddebug):
        Modules: bar.py
"""
        self.assertRaises(ValueError, lambda: parse_and_analyse(data))

    def test_not(self):
        data = """\
Library:
    if not true:
        Modules: foo.py, bar.py
    else:
        Modules:  fubar.py
"""

        self.ref["libraries"]["default"].update({"py_modules": ["fubar.py"]})
        self.assertEqual(parse_and_analyse(data), self.ref)

class TestExecutable(unittest.TestCase):
    def setUp(self):
        self.ref = _empty_description()

    def test_modules(self):
        data = """\
Executable: foo
    Module: foo.bar
    Function: main
"""
        self.ref["executables"] = {"foo": {"module": "foo.bar",
                                           "function": "main",
                                           "name": "foo"}}
        self.assertEqual(parse_and_analyse(data), self.ref)
