import ply

from unittest \
    import \
        TestCase
from nose.tools \
    import \
        assert_equal, assert_raises

from toydist.core.parser.lexer \
    import \
        MyLexer, indent_generator

def split(s):
    ret = []
    for i in s.split(" "):
        ret.extend(i.splitlines())
    return ret

def isstring(s):
    return issubclass(s.__class__, basestring)

class TestLexer(TestCase):
    def setUp(self):
        self.lexer = MyLexer()

    def _test_stage1(self, data, ref):
        self.lexer.input(data)
        self._test_impl(data, ref)

    def _test_stage2(self, data, ref):
        self.lexer.input(data)
        self.lexer.token_stream = indent_generator(self.lexer.token_stream)
        self._test_impl(data, ref)

    def _test_impl(self, data, ref):
        res = []
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            res.append(tok.type)

        if isstring(ref):
            ref = split(ref)
        try:
            assert_equal(res, ref)
        except AssertionError, e:
            cnt = 0
            for i, j in zip(res, ref):
                if not i == j:
                    break
                cnt += 1
            print "Break at index", cnt
            raise e

    def _tokens_stage2(self, data):
        self.lexer.input(data)
        self.lexer.token_stream = indent_generator(self.lexer.token_stream)

        res = []
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            res.append(tok)
        return res

# Test tokenizer stage before indentation generation
class TestLexerStageOne(TestLexer):
    def test_single_line(self):
        data = """\
Name: yo
"""
        ref = ["WORD", "COLON", "WS", "WORD", "NEWLINE"]
        self._test_stage1(data, ref)

    def test_two_lines(self):
        data = """\
Name: yo
Summary: a brief summary
"""
        ref = ["WORD", "COLON", "WS", "WORD", "NEWLINE",
               "WORD", "COLON", "WS", "WORD", "WS", "WORD", "WS", "WORD", "NEWLINE"]
        self._test_stage1(data, ref)

    def test_tab(self):
        data = """\
Library:
\tpackages
"""
        assert_raises(SyntaxError, lambda: self._test_stage1(data, []))

class TestLexerStageTwo(TestLexer):
    def test_single_line(self):
        data = """\
Name: yo
"""
        ref = ["WORD", "COLON", "WS", "WORD", "NEWLINE"]
        self._test_stage2(data, ref)

    def test_two_lines(self):
        data = """\
Name: yo
Summary: a brief summary
"""
        ref = ["WORD", "COLON", "WS", "WORD", "NEWLINE",
               "WORD", "COLON", "WS", "WORD", "WS", "WORD", "WS", "WORD", "NEWLINE"]
        self._test_stage2(data, ref)

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
        self._test_stage2(data, ref)

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
        self._test_stage2(data, ref)

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
        self._test_stage2(data, ref)

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
        self._test_stage2(data, ref)

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
        self._test_stage2(data, ref)

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
WORD DOT WORD NEWLINE
DEDENT
WORD COLON NEWLINE
INDENT WORD DOT WORD NEWLINE
DEDENT
WORD COLON WS WORD NEWLINE
DEDENT
"""
        self._test_stage2(data, ref)

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
WORD DOT WORD NEWLINE
DEDENT
WORD COLON NEWLINE
INDENT WORD DOT WORD NEWLINE
WORD DOT WORD NEWLINE
DEDENT DEDENT
WORD COLON WS WORD NEWLINE
WORD COLON WS WORD NEWLINE
"""
        self._test_stage2(data, ref)

    def test_indent_value(self):
        data = """\
Description: some
    words and whatnot
      .
"""
        ref = """\
WORD COLON WS WORD NEWLINE
INDENT WORD WS WORD WS WORD NEWLINE
INDENT DOT NEWLINE
DEDENT DEDENT
"""
        self._test_stage2(data, ref)
        tokens = self._tokens_stage2(data)

        indents = [t for t in tokens if t.type in ["INDENT", "DEDENT"]]
        assert_equal(indents[0].value, 4)
        assert_equal(indents[1].value, 6)
        assert_equal(indents[2].value, 6)
        assert_equal(indents[3].value, 4)

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
INDENT DOT NEWLINE
DEDENT DEDENT
WORD COLON WS WORD NEWLINE
"""
        self._test_stage2(data, ref)
        tokens = self._tokens_stage2(data)

        indents = [t for t in tokens if t.type in ["INDENT", "DEDENT"]]
        assert_equal(indents[0].value, 4)
        assert_equal(indents[1].value, 6)
        assert_equal(indents[2].value, 6)
        assert_equal(indents[3].value, 4)
