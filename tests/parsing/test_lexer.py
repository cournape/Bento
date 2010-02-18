import ply

from unittest \
    import \
        TestCase
from nose.tools \
    import \
        assert_equal, assert_raises

from toydist.core.parser.lexer \
    import \
        MyLexer

class TestLexer(TestCase):
    def setUp(self):
        self.lexer = MyLexer()

    def _test_stage1(self, data, ref):
        self.lexer.input(data)
        self._test_impl(data, ref)

    def _test_impl(self, data, ref):
        res = []
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            res.append(tok.type)
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

    def _tokens(self, data):
        self.lexer.input(data)

        res = []
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            res.append(tok)
        return res

# Test tokenizer stage before indentation generation
class TestRawLexer(TestLexer):
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
