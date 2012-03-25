from bento.compat.api.moves import unittest

from bento.convert.utils \
    import \
        canonalize_path

class TestCanonalizePath(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(canonalize_path(r"foo\bar"), "foo/bar")
