from unittest \
    import \
        TestCase

from bento.core.utils \
    import \
        extract_exception, is_string
from bento.core.parser.lexer \
    import \
        MyLexer, indent_generator, post_process

def split(s):
    ret = []
    for i in s.split(" "):
        ret.extend(i.splitlines())
    return ret

class TestLexer(TestCase):
    def setUp(self):
        self.lexer = MyLexer()

    def _test(self, data, ref):
        self.lexer.input(data)
        self._test_impl(data, ref)

    def _test_impl(self, data, ref):
        res = []
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            res.append(tok.type)

        if is_string(ref):
            ref = split(ref)
        try:
            self.assertEqual(res, ref)
        except AssertionError:
            e = extract_exception()
            cnt = 0
            for i, j in zip(res, ref):
                if not i == j:
                    break
                cnt += 1
            print("Break at index %d" % cnt)
            raise e

    def _get_tokens(self, data):
        self.lexer.input(data)
        return [t for t in self.lexer.token_stream]

# Test tokenizer stage before indentation generation
class TestLexerStageOne(TestLexer):
    def setUp(self):
        self.lexer = MyLexer(stage="raw")

    def test_single_line(self):
        data = """\
Name: yo
"""
        ref = ["WORD", "COLON", "WS", "WORD", "NEWLINE"]
        self._test(data, ref)

    def test_two_lines(self):
        data = """\
Name: yo
Summary: a brief summary
"""
        ref = ["WORD", "COLON", "WS", "WORD", "NEWLINE",
               "WORD", "COLON", "WS", "WORD", "WS", "WORD", "WS", "WORD", "NEWLINE"]
        self._test(data, ref)

    def test_tab(self):
        data = """\
Library:
\tpackages
"""
        self.assertRaises(SyntaxError, lambda: self._test(data, []))

class TestLexerStageTwo(TestLexer):
    def setUp(self):
        self.lexer = MyLexer(stage="escape_detected")

    def test_simple(self):
        data = "yoyo"
        ref = "WORD"
        self._test(data, ref)

    def test_empty(self):
        data = ""
        ref = []
        self._test(data, ref)

    def test_simple_escape(self):
        data = "yoyo\ "
        ref = "WORD WS"
        self._test(data, ref)

        tokens = self._get_tokens(data)
        self.assertEqual(tokens[0].escaped, False)
        self.assertEqual(tokens[1].escaped, True)

    def test_double_escape(self):
        data = "yoyo\\\\ "
        ref = "WORD BACKSLASH WS"
        self._test(data, ref)

        tokens = self._get_tokens(data)
        self.assertEqual(tokens[0].escaped, False)
        self.assertEqual(tokens[1].escaped, True)
        self.assertEqual(tokens[2].escaped, False)

    def test_wrong_escape(self):
        data = "yoyo\\"
        def f():
            self._get_tokens(data)
        self.assertRaises(SyntaxError, f)

class TestLexerStageThree(TestLexer):
    def setUp(self):
        self.lexer = MyLexer(stage="escape_merged")

    def test_simple(self):
        data = "yoyo"
        ref = "WORD"
        self._test(data, ref)

    def test_empty(self):
        data = ""
        ref = []
        self._test(data, ref)

    def test_simple_escape(self):
        data = "yoyo\ "
        ref = "WORD"
        self._test(data, ref)

        tokens = self._get_tokens(data)
        self.assertEqual(tokens[0].value, "yoyo ")

    def test_simple_escape2(self):
        data = "\ yoyo\ "
        ref = "WORD"
        self._test(data, ref)

        tokens = self._get_tokens(data)
        self.assertEqual(tokens[0].value, " yoyo ")

    def test_double_escape(self):
        data = "yoyo\ \ yaya"
        ref = "WORD"
        self._test(data, ref)

        tokens = self._get_tokens(data)
        self.assertEqual(tokens[0].value, "yoyo  yaya")

    def test_literal_escape(self):
        data = "yoyo\\\\"
        ref = "WORD"
        self._test(data, ref)

        tokens = self._get_tokens(data)
        self.assertEqual(tokens[0].value, "yoyo\\")

class TestLexerStageFour(TestLexer):
    def setUp(self):
        self.lexer = MyLexer(stage="indent_generated")

    def test_single_line(self):
        data = """\
Name: yo
"""
        ref = ["WORD", "COLON", "WS", "WORD", "NEWLINE"]
        self._test(data, ref)

    def test_two_lines(self):
        data = """\
Name: yo
Summary: a brief summary
"""
        ref = ["WORD", "COLON", "WS", "WORD", "NEWLINE",
               "WORD", "COLON", "WS", "WORD", "WS", "WORD", "WS", "WORD", "NEWLINE"]
        self._test(data, ref)

    def test_simple_indent(self):
        data = """\
Packages:
    yo
"""
        ref = """\
WORD COLON NEWLINE
INDENT WORD NEWLINE
DEDENT
"""
        self._test(data, ref)

    def test_simple_indent2(self):
        data = """\
Packages:
    yo,
    yeah
"""
        ref = """\
WORD COLON NEWLINE
INDENT
WORD COMMA NEWLINE
WORD NEWLINE
DEDENT"""
        self._test(data, ref)

    def test_indent_newlines(self):
        data = """\
Description:
    some
    words

    and then more
"""
        ref = """\
WORD COLON NEWLINE
INDENT
WORD NEWLINE
WORD NEWLINE
WORD WS WORD WS WORD NEWLINE
DEDENT
"""
        self._test(data, ref)

    def test_double_indentation(self):
        data = """\
Description:
    some
     words
"""
        ref = """\
WORD COLON NEWLINE
INDENT
WORD NEWLINE
INDENT
WORD NEWLINE
DEDENT DEDENT
"""
        self._test(data, ref)

    def test_simple_dedent(self):
        data = """\
Packages:
    some
Name: words
"""
        ref = """\
WORD COLON NEWLINE
INDENT WORD NEWLINE DEDENT
WORD COLON WS WORD NEWLINE
"""
        self._test(data, ref)

    def test_simple_indent_dedent(self):
        data = """\
Library:
    Packages:
        yo
        yo.foo
    Modules:
        foo.py
    Extension: _bar
"""
        ref = """\
WORD COLON NEWLINE
INDENT
WORD COLON NEWLINE
INDENT
WORD NEWLINE
WORD NEWLINE
DEDENT
WORD COLON NEWLINE
INDENT WORD NEWLINE
DEDENT
WORD COLON WS WORD NEWLINE
DEDENT
"""
        self._test(data, ref)

    def test_complex_indent(self):
        data = """\
Library:
    Packages:
        yo
        yo.foo
    Modules:
        foo.py
        bar.py
Extension: yeah
Extension: yeah2
"""
        ref = """\
WORD COLON NEWLINE
INDENT
WORD COLON NEWLINE
INDENT WORD NEWLINE
WORD NEWLINE
DEDENT
WORD COLON NEWLINE
INDENT WORD NEWLINE
WORD NEWLINE
DEDENT DEDENT
WORD COLON WS WORD NEWLINE
WORD COLON WS WORD NEWLINE
"""
        self._test(data, ref)

    def test_indent_value(self):
        data = """\
Description: some
    words and whatnot
      .
"""
        ref = """\
WORD COLON WS WORD NEWLINE
INDENT WORD WS WORD WS WORD NEWLINE
INDENT WORD NEWLINE
DEDENT DEDENT
"""
        self._test(data, ref)
        tokens = self._get_tokens(data)

        indents = [t for t in tokens if t.type in ["INDENT", "DEDENT"]]
        self.assertEqual(indents[0].value, 4)
        self.assertEqual(indents[1].value, 6)
        self.assertEqual(indents[2].value, 6)
        self.assertEqual(indents[3].value, 4)

    def test_indent_value2(self):
        data = """\
Description: some
    words and whatnot
      .
Name: yo
"""
        ref = """\
WORD COLON WS WORD NEWLINE
INDENT WORD WS WORD WS WORD NEWLINE
INDENT WORD NEWLINE
DEDENT DEDENT
WORD COLON WS WORD NEWLINE
"""
        self._test(data, ref)
        tokens = self._get_tokens(data)

        indents = [t for t in tokens if t.type in ["INDENT", "DEDENT"]]
        self.assertEqual(indents[0].value, 4)
        self.assertEqual(indents[1].value, 6)
        self.assertEqual(indents[2].value, 6)
        self.assertEqual(indents[3].value, 4)

class TestLexerStageFive(TestLexer):
    def setUp(self):
        self.lexer = MyLexer(stage='post_processed')

    def test_single_line(self):
        data = """\
Name: yo
"""
        ref = ["NAME_ID", "COLON", "WORD"]
        self._test(data, ref)

    def test_two_lines(self):
        data = """\
Name: yo
Summary: a brief summary
"""
        ref = ["NAME_ID", "COLON", "WORD",
               "SUMMARY_ID", "COLON", "WS", "WORD", "WS", "WORD", "WS", "WORD"]
        self._test(data, ref)

    def test_simple_indent(self):
        data = """\
Packages:
    yo
"""
        ref = ["PACKAGES_ID", "COLON",
               "INDENT", "WORD", "DEDENT"]
        self._test(data, ref)

    def test_simple_indent2(self):
        data = """\
Packages:
    yo,
    yeah
"""
        ref = ["PACKAGES_ID", "COLON",
               "INDENT",
               "WORD", "COMMA",
               "WORD",
               "DEDENT"]
        self._test(data, ref)

    def test_indent_newlines(self):
        data = """\
Description:
    some
    words

    and then more
"""
        ref = ["DESCRIPTION_ID", "COLON", "NEWLINE",
               "INDENT", "WORD", "NEWLINE",
               "WORD", "NEWLINE",
               "WORD", "WS", "WORD", "WS", "WORD",
               "DEDENT"]
        self._test(data, ref)

    def test_double_indentation(self):
        data = """\
Description:
    some
     words
"""
        ref = ["DESCRIPTION_ID", "COLON", "NEWLINE",
               "INDENT", "WORD", "NEWLINE",
               "INDENT", "WORD",
               "DEDENT", "DEDENT"]
        self._test(data, ref)

    def test_simple_dedent(self):
        data = """\
Packages:
    some
Name: words
"""
        ref = ["PACKAGES_ID", "COLON",
               "INDENT", "WORD", "DEDENT",
               "NAME_ID", "COLON", "WORD"]
        self._test(data, ref)

    def test_simple_indent_dedent(self):
        data = """\
Library:
    Packages:
        yo
        yo.foo
    Modules:
        foo.py
    Extension: _bar
"""
        ref = ["LIBRARY_ID", "COLON",
               "INDENT",
               "PACKAGES_ID", "COLON",
               "INDENT",
               "WORD",
               "WORD",
               "DEDENT",
               "MODULES_ID", "COLON",
               "INDENT", "WORD",
               "DEDENT",
               "EXTENSION_ID", "COLON", "WORD",
               "DEDENT"]
        self._test(data, ref)

    def test_complex_indent(self):
        data = """\
Library:
    Packages:
        yo
        yo.foo
    Modules:
        foo.py
        bar.py
Extension: yeah
Extension: yeah2
"""
        ref = ["LIBRARY_ID", "COLON",
               "INDENT",
               "PACKAGES_ID", "COLON",
               "INDENT", "WORD",
               "WORD",
               "DEDENT",
               "MODULES_ID", "COLON",
               "INDENT", "WORD",
               "WORD",
               "DEDENT", "DEDENT",
               "EXTENSION_ID", "COLON", "WORD",
               "EXTENSION_ID", "COLON", "WORD"]
        self._test(data, ref)

    def test_indent_value(self):
        data = """\
Description: some
    words and whatnot
      .
"""
        ref = ["DESCRIPTION_ID", "COLON", "WS", "WORD", "NEWLINE",
               "INDENT", "WORD", "WS", "WORD", "WS", "WORD", "NEWLINE",
               "INDENT", "WORD",
               "DEDENT", "DEDENT"]
        self._test(data, ref)
        tokens = self._get_tokens(data,)

        indents = [t for t in tokens if t.type in ["INDENT", "DEDENT"]]
        self.assertEqual(indents[0].value, 4)
        self.assertEqual(indents[1].value, 6)
        self.assertEqual(indents[2].value, 6)
        self.assertEqual(indents[3].value, 4)

    def test_indent_value2(self):
        data = """\
Description: some
    words and whatnot
      .
Name: yo
"""
        ref = ["DESCRIPTION_ID", "COLON", "WS", "WORD", "NEWLINE",
               "INDENT", "WORD", "WS", "WORD", "WS", "WORD", "NEWLINE",
               "INDENT", "WORD",
               "DEDENT", "DEDENT",
               "NAME_ID", "COLON", "WORD"]
        self._test(data, ref)
        tokens = self._get_tokens(data,)

        indents = [t for t in tokens if t.type in ["INDENT", "DEDENT"]]
        self.assertEqual(indents[0].value, 4)
        self.assertEqual(indents[1].value, 6)
        self.assertEqual(indents[2].value, 6)
        self.assertEqual(indents[3].value, 4)

    def test_comma(self):
        data = """\
Library:
    Packages:
        yo,
        bar,
        yo
"""
        ref = ["LIBRARY_ID", "COLON",
               "INDENT", "PACKAGES_ID", "COLON",
               "INDENT", "WORD", "COMMA",
               "WORD", "COMMA",
               "WORD",
               "DEDENT",
               "DEDENT"
               ]
        self._test(data, ref)

    def test_comma2(self):
        data = """\
Library:
    Packages: foo, bar
    Packages:
        foo,
        bar
    Packages: foo,
        bar
"""
        ref = ["LIBRARY_ID", "COLON",
               "INDENT",
               "PACKAGES_ID", "COLON", "WORD", "COMMA", "WORD",
               "PACKAGES_ID", "COLON", "INDENT", "WORD", "COMMA", "WORD", "DEDENT",
               "PACKAGES_ID", "COLON", "WORD", "COMMA", "INDENT", "WORD",
               "DEDENT",
               "DEDENT"]
        self._test(data, ref)

    def test_tab(self):
        data = """\
Library:
\tpackages
"""
        self.assertRaises(SyntaxError, lambda: self._test(data, []))

    def test_rest_literal1(self):
        data = '''\
Description:
    Sphinx is a tool that makes it easy to create intelligent and beautiful
    documentation for Python projects (or other documents consisting of
    multiple reStructuredText sources), written by Georg Brandl.
    It was originally created to translate the new Python documentation,
    but has now been cleaned up in the hope that it will be useful to many
    other projects.
'''
        ref_str = """\
DESCRIPTION_ID COLON NEWLINE
INDENT
    WORD WS WORD WS WORD WS WORD WS WORD WS WORD WS WORD WS WORD WS WORD WS
    WORD WS WORD WS WORD WS WORD
NEWLINE
    WORD WS WORD WS WORD WS WORD WS LPAR WORD WS WORD WS WORD WS WORD WS WORD
NEWLINE
    WORD WS WORD WS WORD RPAR COMMA WS WORD WS WORD WS WORD WS WORD
NEWLINE
    WORD WS WORD WS WORD WS WORD WS WORD WS WORD WS WORD WS WORD WS WORD WS
    WORD COMMA
NEWLINE
    WORD WS WORD WS WORD WS WORD WS WORD WS WORD WS WORD WS WORD WS WORD WS
    WORD WS WORD WS WORD WS WORD WS WORD WS WORD WS WORD NEWLINE WORD WS WORD
DEDENT
"""

        self._test(data, split(ref_str))

        data = """
Description:
    Sphinx uses reStructuredText as its markup language, and many of its strengths
    come from the power and straightforwardness of reStructuredText and its
    parsing and translating suite, the Docutils.
"""
        ref_str = """\
DESCRIPTION_ID COLON NEWLINE
INDENT
    WORD WS WORD WS WORD WS WORD WS WORD WS WORD WS WORD COMMA WS WORD WS WORD
    WS WORD WS WORD WS WORD
NEWLINE
    WORD WS WORD WS WORD WS WORD WS WORD WS WORD WS WORD WS WORD WS WORD WS WORD
NEWLINE
    WORD WS WORD WS WORD WS WORD COMMA WS WORD WS WORD
DEDENT
"""
        self._test(data, split(ref_str))
    
        data = """\
Description:
    Although it is still under constant development, the following features
    are already present, work fine and can be seen "in action" in the Python docs:
"""

        ref_str = """\
DESCRIPTION_ID COLON NEWLINE
INDENT
    WORD WS WORD WS WORD WS WORD WS WORD WS WORD WS WORD COMMA WS WORD WS WORD
    WS WORD
NEWLINE
    WORD WS WORD WS WORD COMMA WS WORD WS WORD WS WORD WS WORD WS WORD WS WORD
    WS WORD WS WORD WS WORD WS WORD WS WORD WS WORD COLON
DEDENT
"""

        self._test(data, split(ref_str))

        data = """\
Description:
    * Output formats: HTML (including Windows HTML Help), plain text and LaTeX,
      for printable PDF versions
"""

        ref_str = """\
DESCRIPTION_ID COLON NEWLINE
INDENT
    WORD WS WORD WS WORD COLON WS WORD WS LPAR WORD WS WORD WS WORD WS WORD RPAR
    COMMA WS WORD WS WORD WS WORD WS WORD COMMA
NEWLINE
    INDENT WORD WS WORD WS WORD WS WORD
DEDENT
DEDENT
"""

        self._test(data, split(ref_str))

#    def test_rest_literal2(self):
#        data = '''\
#Description:
#    Sphinx is a tool that makes it easy to create intelligent and beautiful
#    documentation for Python projects (or other documents consisting of
#    multiple reStructuredText sources), written by Georg Brandl.
#    It was originally created to translate the new Python documentation,
#    but has now been cleaned up in the hope that it will be useful to many
#    other projects.
#
#    Sphinx uses reStructuredText as its markup language, and many of its strengths
#    come from the power and straightforwardness of reStructuredText and its
#    parsing and translating suite, the Docutils.
#
#    Although it is still under constant development, the following features
#    are already present, work fine and can be seen "in action" in the Python docs:
#
#    * Output formats: HTML (including Windows HTML Help), plain text and LaTeX,
#      for printable PDF versions
#    * Extensive cross-references: semantic markup and automatic links
#      for functions, classes, glossary terms and similar pieces of information
#    * Hierarchical structure: easy definition of a document tree, with automatic
#      links to siblings, parents and children
#    * Automatic indices: general index as well as a module index
#    * Code handling: automatic highlighting using the Pygments highlighter
#    * Various extensions are available, e.g. for automatic testing of snippets
#      and inclusion of appropriately formatted docstrings.
#
#    A development egg can be found `here
#    <http://bitbucket.org/birkenfeld/sphinx/get/tip.gz#egg=Sphinx-dev>`_.
#'''

    def test_ref_literal2(self):
        # Test transition from SCANING_MULTILINE_FIELD
        data = """\
Description: a summary
Name: yo
"""
        ref_str = """\
DESCRIPTION_ID COLON WS WORD WS WORD
NAME_ID COLON WORD
"""
        self._test(data, split(ref_str))

    def test_indented_multiline(self):
        data = """\
Path: path
    Description: descr
    Name: name
"""

        ref_str = """\
PATH_ID COLON WORD
INDENT
DESCRIPTION_ID COLON WS WORD
NAME_ID COLON WORD
DEDENT
"""
        self._test(data, split(ref_str))

    def test_indented_multiline2(self):
        data = """\
Classifiers:
    foo
Path: path
    Description: descr
    Name: name
"""

        ref_str = """\
CLASSIFIERS_ID COLON
INDENT
WORD
DEDENT
PATH_ID COLON WORD
INDENT
DESCRIPTION_ID COLON WS WORD
NAME_ID COLON WORD
DEDENT
"""
        self._test(data, split(ref_str))

class TestNewLines(TestLexer):
    def setUp(self):
        self.lexer = MyLexer(stage="post_processed")

    # Test we throw away NEWLINES except in literals
    def test_lastnewline(self):
        data = """\
Name: yo
"""
        ref_str = """\
NAME_ID COLON WORD
"""
        self._test(data, split(ref_str))

    def test_start_with_newlines(self):
        data = """\

Name: yo
"""
        ref_str = """\
NAME_ID COLON WORD
"""
        self._test(data, split(ref_str))

    def test_start_with_newlines2(self):
        data = """\
Summary: a summary
"""
        ref_str = """\
SUMMARY_ID COLON WS WORD WS WORD
"""
        self._test(data, split(ref_str))

    def test_dedent_newline(self):
        data = """\
Description: Sphinx
    is
        a
    tool
"""

        ref_str = """\
DESCRIPTION_ID COLON WS WORD NEWLINE
INDENT WORD NEWLINE
INDENT WORD NEWLINE
DEDENT WORD
DEDENT
"""
        self._test(data, split(ref_str))

    def test_single_line(self):
        data = "Name: word"

        ref_str = "NAME_ID COLON WORD"
        self._test(data, split(ref_str))

class TestComment(TestLexer):
    def setUp(self):
        self.lexer = MyLexer(stage="post_processed")

    def test_simple(self):
        data = """\
# Simple comment
Name: foo
"""

        ref_str = "NAME_ID COLON WORD"
        self._test(data, split(ref_str))

    def test_simple_inline(self):
        data = """\
Name: foo # inline comment
"""

        ref_str = "NAME_ID COLON WORD"
        self._test(data, split(ref_str))

    def test_simple_inline2(self):
        data = """\
ExtraSourceFiles:
    # indented comment
    foo
"""

        ref_str = "EXTRA_SOURCE_FILES_ID COLON INDENT WORD DEDENT"
        self._test(data, split(ref_str))
