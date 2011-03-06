import os
import sys
import unittest

from nose.tools \
    import \
        assert_equal, assert_true

from bento.core.node \
    import \
        Node, NodeWithBuild, create_root_with_source_tree

def get_root():
    # FIXME: not exactly...
    if sys.platform == "win32":
        return ""
    else:
        return "/"

class TestNode(unittest.TestCase):
    def setUp(self):
        self.root = Node("", None)
        self.cur = self.root.make_node(os.getcwd())

    def test_scratch_creation(self):
        root = Node("", None)
        assert_equal(root.abspath(), get_root())

    def test_find_node(self):
        node_abspath = os.path.normpath(self.cur.abspath())
        r_node_abspath = os.path.abspath(os.getcwd())
        assert_true(node_abspath, r_node_abspath)

class TestNodeWithBuild(unittest.TestCase):
    def setUp(self):
        top = os.getcwd()
        build = os.path.join(os.getcwd(), "_tmp_build")

        self.root = create_root_with_source_tree(top, build)

    def test_root(self):
        assert_equal(self.root.abspath(), get_root())

    def test_cwd_node(self):
        cur_node = self.root.make_node(os.getcwd())
        assert_equal(os.getcwd(), cur_node.abspath())
