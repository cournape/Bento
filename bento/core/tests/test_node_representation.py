import os
import tempfile
import shutil

from bento.compat.api.moves \
    import \
        unittest

from bento.core.package \
    import \
        PackageDescription
from bento.core.node_package \
    import \
        NodeRepresentation
from bento.core.node \
    import \
        create_root_with_source_tree
from bento.core.testing \
    import \
        create_fake_package_from_bento_info

class TestNodeRepresentation(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.root = create_root_with_source_tree(self.d, os.path.join(self.d, "build"))
        self.top_node = self.root.find_node(self.d)

        self.old_dir = os.getcwd()
        os.chdir(self.d)

    def tearDown(self):
        os.chdir(self.old_dir)
        shutil.rmtree(self.d)

    def test_simple(self):
        bento_info = """\
Name: foo

Library:
    Extension: _foo
        Sources: src/foo.c, src/bar.c
"""
        create_fake_package_from_bento_info(self.top_node, bento_info)

        bento_info = """\
Name: foo

Library:
    Extension: _foo
        Sources: src/foo.c, src/bar.c
"""
        pkg = PackageDescription.from_string(bento_info)
        node_pkg = NodeRepresentation(self.top_node, self.top_node)
        node_pkg.update_package(pkg)

        extensions = dict(node_pkg.iter_category("extensions"))
        self.assertEqual(len(extensions), 1)
        self.assertEqual(len(extensions["_foo"].nodes), 2)

    def test_sources_glob(self):
        bento_info = """\
Name: foo

Library:
    Extension: _foo
        Sources: src/foo.c, src/bar.c
"""
        create_fake_package_from_bento_info(self.top_node, bento_info)

        bento_info = """\
Name: foo

Library:
    Extension: _foo
        Sources: src/*.c
"""
        pkg = PackageDescription.from_string(bento_info)
        node_pkg = NodeRepresentation(self.top_node, self.top_node)
        node_pkg.update_package(pkg)

        extensions = dict(node_pkg.iter_category("extensions"))
        self.assertEqual(len(extensions), 1)
        self.assertEqual(len(extensions["_foo"].nodes), 2)
