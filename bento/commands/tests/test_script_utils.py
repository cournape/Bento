from bento.compat.api.moves \
    import \
        unittest
from bento.commands.script_utils \
    import \
        nt_quote_arg

class TestMisc(unittest.TestCase):
    def test_nt_quote_arg(self):
        s = nt_quote_arg("foo")
        self.assertEqual(s, "foo")

        s = nt_quote_arg(" foo")
        self.assertEqual(s, '" foo"')

        s = nt_quote_arg("\ foo")
        self.assertEqual(s, '"\\ foo"')
