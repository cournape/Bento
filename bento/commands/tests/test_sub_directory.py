import os
import os.path as op
import tempfile
import shutil
import unittest

from bento.core.errors \
    import \
        InvalidPackage
from bento.core \
    import \
        PackageDescription
from bento.core.node \
    import \
        create_root_with_source_tree
from bento.core.node_package \
    import \
        NodeRepresentation
from bento.core.testing \
    import \
        create_fake_package_from_bento_info
from bento.commands.tests.utils \
    import \
        prepare_configure, prepare_build
from bento.installed_package_description \
    import \
        InstalledSection

from bento.commands.tests.utils \
    import \
        comparable_installed_sections
from bento.core.testing \
    import \
        require_c_compiler

class TestSubDirectory(unittest.TestCase):
    def setUp(self):
        self.old_dir = os.getcwd()

        self.d = tempfile.mkdtemp()
        self.root = create_root_with_source_tree(self.d, os.path.join(self.d, "build"))
        self.run_node = self.root.find_node(self.d)
        self.top_node = self.run_node

        os.chdir(self.d)

    def tearDown(self):
        os.chdir(self.old_dir)
        shutil.rmtree(self.d)

    def test_recurse(self):
        """Check that we raise a proper exception when mixing recurse and
        sub_directory features."""
        bento_info = """\
Name: foo

Recurse: bar

Library:
    SubDirectory: lib
"""
        self.assertRaises(InvalidPackage, lambda: PackageDescription.from_string(bento_info))

    def _test_installed_sections(self, bento_info, r_sections):
        create_fake_package_from_bento_info(self.top_node, bento_info)

        conf, configure = prepare_configure(self.run_node, bento_info)
        configure.run(conf)
        conf.shutdown()

        bld, build = prepare_build(self.top_node, conf.pkg, conf.package_options)
        build.run(bld)
        bld.shutdown()

        sections = bld.section_writer.sections

        self.assertEqual(comparable_installed_sections(sections),
                         comparable_installed_sections(r_sections))

    def test_packages(self):
        """Test sub_directory support for packages."""
        self.maxDiff = 1024

        bento_info = """\
Name: foo

Library:
    SubDirectory: lib
    Packages: foo
"""

        r_section = InstalledSection.from_source_target_directories("pythonfiles",
                                     "foo",
                                     "$_srcrootdir/../lib",
                                     "$sitedir",
                                     ["foo/__init__.py"])
        r_sections = {"pythonfiles":
                         {"foo": r_section}}
        self._test_installed_sections(bento_info, r_sections)

    @require_c_compiler("yaku")
    def test_extension(self):
        """Test sub_directory support for C extensions."""
        bento_info = """\
Name: foo

Library:
    SubDirectory: lib
    Extension: foo
        Sources: src/foo.c
"""

        r_section = InstalledSection.from_source_target_directories("extensions",
                                     "foo",
                                     "$_srcrootdir/.",
                                     "$sitedir/",
                                     ["foo.so"])
        r_sections = {"extensions":
                        {"foo":
                            r_section}}
        self._test_installed_sections(bento_info, r_sections)

    @require_c_compiler("yaku")
    def test_compiled_library(self):
        """Test sub_directory support for C compiled libraries."""
        bento_info = """\
Name: foo

Library:
    SubDirectory: lib
    CompiledLibrary: foo
        Sources: src/foo.c
"""

        r_section = InstalledSection.from_source_target_directories("compiled_libraries",
                                     "foo",
                                     "$_srcrootdir/.",
                                     "$sitedir/",
                                     ["libfoo.a"])
        r_sections = {"compiled_libraries":
                         {"foo": r_section}}
        self._test_installed_sections(bento_info, r_sections)

    def test_module(self):
        """Test sub_directory support for python module."""
        bento_info = """\
Name: foo

Library:
    SubDirectory: lib
    Modules: foo
"""

        r_section = InstalledSection.from_source_target_directories("pythonfiles",
                                     "foo",
                                     "$_srcrootdir/../lib",
                                     "$sitedir",
                                     ["foo.py"])
        r_sections = {"pythonfiles":
                         {"foo": r_section}}
        self._test_installed_sections(bento_info, r_sections)
