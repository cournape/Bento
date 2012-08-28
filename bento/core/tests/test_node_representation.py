import os
import tempfile
import shutil

import os.path as op

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

    def test_iter_source_nodes(self):
        r_files = set([op.join("src", "foo.c"),
            op.join("src", "bar.c"),
            op.join("src", "fubar.c"),
            op.join("foo", "__init__.py"),
            op.join("foo", "bar", "__init__.py"),
            "fu.py", "foo.1"])

        bento_info = """\
Name: foo

DataFiles: foo
    TargetDir: $sharedir
    Files: foo.1

Library:
    Extension: _foo
        Sources: src/foo.c, src/bar.c
    CompiledLibrary: fubar
        Sources: src/fubar.c
    Packages: foo, foo.bar
    Modules: fu
"""
        create_fake_package_from_bento_info(self.top_node, bento_info)

        package = PackageDescription.from_string(bento_info)
        node_package = NodeRepresentation(self.top_node, self.top_node)
        node_package.update_package(package)

        files = set(n.path_from(self.top_node) for n in node_package.iter_source_nodes())
        self.assertEqual(files, r_files)
