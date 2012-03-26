import os
import shutil
import tempfile

import os.path as op

from bento.compat.api.moves \
    import \
        unittest
from bento.core \
    import \
        PackageDescription, PackageOptions
from bento.core.errors \
    import \
        InvalidPackage
from bento.core.node \
    import \
        create_root_with_source_tree
from bento.core.node_package \
    import \
        NodeRepresentation
from bento.commands.hooks \
    import \
        create_hook_module, find_pre_hooks
from bento.commands.context \
    import \
        ConfigureYakuContext
from bento.installed_package_description \
    import \
        InstalledSection

from bento.core.testing \
    import \
        create_fake_package_from_bento_infos
from bento.commands.tests.utils \
    import \
        prepare_configure, prepare_build, comparable_installed_sections

def comparable_representation(top_node, node_pkg):
    """Return a dictionary representing the node_pkg to be used for
    comparison."""
    d = {"packages": {}, "extensions": {}}
    for k, v in node_pkg.iter_category("extensions"):
        d["extensions"][k] = v.extension_from(top_node)
    for k, v in node_pkg.iter_category("packages"):
        d["packages"][k] = (v.full_name, v.nodes, v.top_node, v.top_or_lib_node)
    return d

class TestRecurseBase(unittest.TestCase):
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

    def _create_package_and_reference(self, bento_info, r_bento_info):
        pkg = PackageDescription.from_string(bento_info)
        node_pkg = NodeRepresentation(self.run_node, self.top_node)
        node_pkg.update_package(pkg)

        r_pkg = PackageDescription.from_string(r_bento_info)
        r_node_pkg = NodeRepresentation(self.run_node, self.top_node)
        r_node_pkg.update_package(r_pkg)

        return node_pkg, r_node_pkg

    def test_py_packages(self):
        run_node = self.run_node

        bento_info = """\
Name: foo

Recurse: bar

Library:
    Packages: bar
"""
        sub_bento_info = """\
Library:
    Packages: foo
"""

        r_bento_info = """\
Name: foo

Library:
    Packages: bar, bar.foo
"""

        bentos = {"bento.info": bento_info,
                  op.join("bar", "bento.info"): sub_bento_info}
        create_fake_package_from_bento_infos(run_node, bentos)

        node_pkg, r_node_pkg = self._create_package_and_reference(bento_info, r_bento_info)
        self.assertEqual(comparable_representation(self.top_node, node_pkg),
                         comparable_representation(self.top_node, r_node_pkg))


    def test_extension(self):
        run_node = self.run_node

        bento_info = """\
Name: foo

Recurse: bar

Library:
    Extension: foo
        Sources: src/foo.c
"""
        sub_bento_info = """\
Library:
    Extension: foo
        Sources: src/foo.c
"""

        r_bento_info = """\
Name: foo

Library:
    Extension: foo
        Sources: src/foo.c
    Extension: bar.foo
        Sources: bar/src/foo.c
"""

        bentos = {"bento.info": bento_info,
                  op.join("bar", "bento.info"): sub_bento_info}
        create_fake_package_from_bento_infos(run_node, bentos)

        node_pkg, r_node_pkg = self._create_package_and_reference(bento_info, r_bento_info)
        self.assertEqual(comparable_representation(self.top_node, node_pkg),
                         comparable_representation(self.top_node, r_node_pkg))

    def test_basics(self):
        run_node = self.run_node

        bento_info = """\
Name: foo

Recurse:
    bar
"""
        bento_info2 = """\
Recurse:
    foo

Library:
    Extension: _foo
        Sources: foo.c
    CompiledLibrary: _bar
        Sources: foo.c
"""

        bento_info3 = """\
Library:
    Packages: sub2
"""
        bentos = {"bento.info": bento_info, os.path.join("bar", "bento.info"): bento_info2,
                  os.path.join("bar", "foo", "bento.info"): bento_info3}
        create_fake_package_from_bento_infos(run_node, bentos)

        r_bento_info = """\
Name: foo

Library:
    Packages:
        bar.foo.sub2
    Extension: bar._foo
        Sources: bar/foo.c
    CompiledLibrary: bar._bar
        Sources: bar/foo.c
"""

        node_pkg, r_node_pkg = self._create_package_and_reference(bento_info, r_bento_info)

        self.assertEqual(comparable_representation(self.top_node, node_pkg),
                         comparable_representation(self.top_node, r_node_pkg))

    def test_py_module_invalid(self):
        """Ensure we get a package error when defining py modules in recursed
        bento.info."""
        bento_info = """\
Name: foo

Recurse: bar
"""
        sub_bento_info = """\
Library:
    Modules: foo
"""
        bentos = {"bento.info": bento_info,
                  os.path.join("bar", "bento.info"): sub_bento_info}
        self.assertRaises(InvalidPackage,
                          lambda: create_fake_package_from_bento_infos(self.run_node, bentos))

    def test_hook(self):
        root = self.root
        top_node = self.top_node

        bento_info = """\
Name: foo

HookFile:
    bar/bscript

Recurse:
    bar
"""
        bento_info2 = """\
Library:
    Packages: fubar
"""

        bscript = """\
from bento.commands import hooks
@hooks.pre_configure
def configure(ctx):
    packages = ctx.local_pkg.packages
    ctx.local_node.make_node("test").write(str(packages))
"""
        bentos = {"bento.info": bento_info, os.path.join("bar", "bento.info"): bento_info2}
        bscripts = {os.path.join("bar", "bscript"): bscript}
        create_fake_package_from_bento_infos(top_node, bentos, bscripts)

        conf, configure = prepare_configure(self.run_node, bento_info, ConfigureYakuContext)
        try:
            hook = top_node.search("bar/bscript")
            m = create_hook_module(hook.abspath())
            for hook in find_pre_hooks([m], "configure"):
                conf.pre_recurse(root.find_dir(hook.local_dir))
                try:
                    hook(conf)
                finally:
                    conf.post_recurse()

            test = top_node.search("bar/test")
            if test:
                self.failUnlessEqual(test.read(), "['fubar']")
            else:
                self.fail("test dummy not found")
        finally:
            configure.shutdown(conf)
            conf.shutdown()

class TestInstalledSections(unittest.TestCase):
    """Test registered installed sections are the expected ones when using
    recursive support."""
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

    def _test_installed_sections(self, bento_infos, r_sections):
        create_fake_package_from_bento_infos(self.top_node, bento_infos)

        conf, configure = prepare_configure(self.run_node, bento_infos["bento.info"])
        configure.run(conf)
        conf.shutdown()

        bld, build = prepare_build(self.top_node, conf.pkg, conf.package_options)
        build.run(bld)
        bld.shutdown()

        sections = bld.section_writer.sections

        self.assertEqual(comparable_installed_sections(sections),
                         comparable_installed_sections(r_sections))

    def test_packages(self):
        bento_info = """\
Name: foo

Recurse:
    foo

Library:
    Packages: foo
"""
        sub_bento_info = """\
Library:
    Packages: bar
"""

        r_bar_section = InstalledSection.from_source_target_directories("pythonfiles",
                                     "foo",
                                     "$_srcrootdir/..",
                                     "$sitedir",
                                     ["foo/__init__.py"])
        r_foo_bar_section = InstalledSection.from_source_target_directories("pythonfiles",
                                     "foo.bar",
                                     "$_srcrootdir/..",
                                     "$sitedir",
                                     ["foo/bar/__init__.py"])
        r_sections = {"pythonfiles":
                         {"foo": r_bar_section,
                          "foo.bar": r_foo_bar_section}}
        self._test_installed_sections({"bento.info": bento_info, op.join("foo", "bento.info"): sub_bento_info},
                                      r_sections)

    def test_extension(self):
        bento_info = """\
Name: foo

Recurse: bar
"""

        sub_bento_info = """\
Library:
    Extension: foo
        Sources: src/foo.c
"""

        r_section = InstalledSection.from_source_target_directories("extensions",
                                     "bar.foo",
                                     "$_srcrootdir/bar",
                                     "$sitedir/bar",
                                     ["foo.so"])
        r_sections = {"extensions":
                        {"bar.foo":
                            r_section}}
        self._test_installed_sections({"bento.info": bento_info, op.join("bar", "bento.info"): sub_bento_info},
                                      r_sections)
