import os
import sys
import pickle

from bento.compat.api.moves \
    import \
        unittest
from bento.core.node \
    import \
        Node, create_root_with_source_tree, find_root, split_path_win32, split_path_cygwin

class TestNode(unittest.TestCase):
    def setUp(self):
        self.root = Node("", None)

        if sys.version_info[0] < 3:
            self._string_classes = [str, unicode]
        else:
            self._string_classes = [str]

    def test_scratch_creation(self):
        root = Node("", None)
        self.assertEqual(root, root)

    def test_find_node(self):
        r_n = os.path.abspath(os.getcwd())

        for f in self._string_classes:
            n = self.root.find_node(f(os.getcwd()))
            self.assertTrue(n)
            assert n.abspath() == r_n

    def test_make_node(self):
        r_n = os.path.abspath(os.getcwd())

        for f in self._string_classes:
            n = self.root.make_node(f(os.getcwd()))
            self.assertTrue(n)
            assert n.abspath() == r_n, "%s vs %s" % (n.abspath(), r_n)

    def test_serialization(self):
        """Test pickled/unpickle round trip."""
        n = self.root.find_node(os.getcwd())
        r_n = pickle.loads(pickle.dumps(n))
        self.assertEqual(n.name, r_n.name)
        self.assertEqual(n.abspath(), r_n.abspath())
        self.assertEqual(n.parent.abspath(), r_n.parent.abspath())
        self.assertEqual([child.abspath() for child in getattr(n, "children", [])],
                         [child.abspath() for child in getattr(n, "children", [])])

class TestNodeWithBuild(unittest.TestCase):
    def setUp(self):
        top = os.getcwd()
        build = os.path.join(os.getcwd(), "_tmp_build")

        self.root = create_root_with_source_tree(top, build)

    def test_root(self):
        self.assertEqual(self.root, find_root(self.root))

    def test_cwd_node(self):
        cur_node = self.root.make_node(os.getcwd())
        self.assertEqual(os.getcwd(), cur_node.abspath())

class TestUtils(unittest.TestCase):
    def test_split_path_win32(self):
        self.assertEqual(split_path_win32(r"C:\foo\bar"), ["C:", "foo", "bar"])
        self.assertEqual(split_path_win32(r"\\"), ["\\"])
        self.assertEqual(split_path_win32(""), [''])

    def test_split_path_cygwin(self):
        self.assertEqual(split_path_cygwin("/foo/bar"), ["", "foo", "bar"])
        self.assertEqual(split_path_cygwin("//"), ["/"])
        self.assertEqual(split_path_cygwin(""), [''])
