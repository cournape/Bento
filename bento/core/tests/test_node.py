import os
import sys
import pickle
import tempfile
import shutil
import copy

import os.path as op

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

    def test_str_repr(self):
        d = tempfile.mkdtemp()
        try:
            r_n = os.path.abspath(os.path.join(d, "foo.txt"))
            node = self.root.make_node(r_n)
            self.assertEqual(str(node), "foo.txt")
            self.assertEqual(repr(node), r_n)
        finally:
            shutil.rmtree(d)

    def test_invalid_copy(self):
        self.assertRaises(NotImplementedError, lambda: copy.copy(self.root))

class TestNodeInsideTemp(unittest.TestCase):
    def setUp(self):
        root = Node("", None)
        self.d_node = root.find_node(tempfile.mkdtemp())
        assert self.d_node is not None

    def tearDown(self):
        shutil.rmtree(self.d_node.abspath())

    def test_delete(self):
        n = self.d_node.make_node("foo.txt")
        n.write("foo")
        self.assertEqual(n.read(), "foo")
        n.delete()
        self.assertEqual(self.d_node.listdir(), [])

    def test_delete_dir(self):
        foo_node = self.d_node.make_node("foo")
        n = foo_node.make_node("bar.txt")
        n.parent.mkdir()
        n.write("foo")
        self.assertEqual(n.read(), "foo")
        foo_node.delete()
        self.assertEqual(self.d_node.listdir(), [])

    def test_mkdir(self):
        bar_node = self.d_node.make_node(op.join("foo", "bar"))
        os.makedirs(bar_node.parent.abspath())
        os.makedirs(bar_node.abspath())
        bar_node.mkdir()

    def test_suffix(self):
        foo = self.d_node.make_node("foo.txt")
        self.assertEqual(foo.suffix(), ".txt")

        foo = self.d_node.make_node("foo.txt.swp")
        self.assertEqual(foo.suffix(), ".swp")

    def test_make_node(self):
        foo = self.d_node.make_node("foo")
        foo.make_node("../bar")
        self.assertTrue(self.d_node.find_node("bar") is not None)

    def test_ant(self):
        for filename in ["bar.txt", "foo.bar", "fubar.txt"]:
            n = self.d_node.make_node(filename)
            n.write("")
        nodes = self.d_node.ant_glob("*.txt")
        bar = self.d_node.find_node("bar.txt")
        fubar = self.d_node.find_node("fubar.txt")
        self.assertEqual(set([fubar.abspath(), bar.abspath()]), set([node.abspath() for node in nodes]))

    def test_ant_excl(self):
        for filename in ["bar.txt", "foo.bar", "fubar.txt"]:
            n = self.d_node.make_node(filename)
            n.write("")
        nodes = self.d_node.ant_glob("*", excl=["*.txt"])
        foobar = self.d_node.find_node("foo.bar")
        self.assertEqual(set(node.abspath() for node in nodes), set([foobar.abspath()]))

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
