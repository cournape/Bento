import os
import tempfile
import shutil

import os.path as op

from bento.core \
    import \
        PackageDescription
from bento.compat.api.moves \
    import \
        unittest
from bento.core.node \
    import \
        create_base_nodes
from bento.core.testing \
    import \
        create_fake_package_from_bento_infos

from bento.commands.utils \
    import \
        has_cython_code

class TestIsUingCython(unittest.TestCase):
    def setUp(self):
        self.old_dir = os.getcwd()

        self.d = tempfile.mkdtemp()
        os.chdir(self.d)

        self.top_node, self.build_node, self.run_node = create_base_nodes()

    def tearDown(self):
        os.chdir(self.old_dir)
        shutil.rmtree(self.d)

    def test_simple_cython(self):
        bento_info = """\
Library:
    Extension: foo
        Sources: foo1.c, foo2.pyx
"""
        bentos = {"bento.info": bento_info}
        create_fake_package_from_bento_infos(self.run_node, bentos)

        pkg = PackageDescription.from_string(bento_info)
        self.assertTrue(has_cython_code(pkg))

    def test_simple_no_cython(self):
        bento_info = """\
Library:
    Extension: foo
        Sources: foo1.c, foo2.c
"""
        bentos = {"bento.info": bento_info}
        create_fake_package_from_bento_infos(self.run_node, bentos)

        pkg = PackageDescription.from_string(bento_info)
        self.assertFalse(has_cython_code(pkg))

    def test_sub_package(self):
        bento_info = """\
Recurse: foo

Library:
    Extension: foo
        Sources: foo1.c
"""
        bento_sub1_info = """
Library:
    Extension: bar
        Sources: bar.pyx
"""
        bentos = {"bento.info": bento_info, op.join("foo", "bento.info"): bento_sub1_info}
        create_fake_package_from_bento_infos(self.run_node, bentos)

        pkg = PackageDescription.from_string(bento_info)
        self.assertTrue(has_cython_code(pkg))
