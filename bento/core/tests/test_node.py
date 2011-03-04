import os
import sys
import unittest

from nose.tools \
    import \
        assert_equal, assert_true

from bento.core.node \
    import \
        Node, NodeWithBuild, create_root_with_source_tree

class TestNode(unittest.TestCase):
    def setUp(self):
        self.root = Node("root", "")
        self.cur = self.root.make_node(os.getcwd())

    def test_scratch_creation(self):
        root = Node("root", "")
        # FIXME: not exactly...
        if sys.platform == "win32":
            drive = os.path.splitdrive(os.getcwd())[0]
            assert_equal(root.abspath(), drive)
        else:
            assert_equal(root.abspath(), "/")

    def test_find_node(self):
        node_abspath = os.path.normpath(self.cur.abspath())
        r_node_abspath = os.path.abspath(os.getcwd())
        assert_true(os.path.samefile(node_abspath, r_node_abspath))

class TestNodeWithBuild(unittest.TestCase):
    def setUp(self):
        top = os.getcwd()
        build = os.path.join(os.getcwd(), "_tmp_build")

        self.root = create_root_with_source_tree(top, build)

    def test_foo(self):
        pass
