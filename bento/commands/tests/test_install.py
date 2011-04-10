import os
import sys
import shutil
import tempfile
import unittest

from bento.core.node \
    import \
        create_root_with_source_tree

from bento.commands.context \
    import \
        BuildContext, BuildYakuContext, ConfigureYakuContext, CmdContext
from bento.commands.tests.utils \
    import \
        prepare_configure, create_fake_package, create_fake_package_from_bento_info, \
        prepare_build
from bento.commands.build \
    import \
        BuildCommand
from bento.commands.install \
    import \
        InstallCommand
from bento.commands.options \
    import \
        OptionsContext, Option

class TestBuildCommand(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.root = create_root_with_source_tree(self.d, os.path.join(self.d, "build"))

        self.old_dir = os.getcwd()
        os.chdir(self.d)

    def tearDown(self):
        os.chdir(self.old_dir)
        shutil.rmtree(self.d)

    def _test_run(self, bento_info):
        root = self.root
        top_node = root.srcnode

        create_fake_package_from_bento_info(top_node, bento_info)

        install_dir = tempfile.mkdtemp()
        cmd_argv = ["--prefix=%s" % install_dir, "--exec-prefix=%s" % install_dir]

        conf, configure = prepare_configure(top_node, bento_info, ConfigureYakuContext, cmd_argv)
        configure.run(conf)
        conf.store()

        bld, build = prepare_build(top_node, conf.pkg)
        build.run(bld)
        build.shutdown(bld)

        install = InstallCommand()
        opts = OptionsContext.from_command(install)

        inst = CmdContext(["--list-files"], opts, conf.pkg, top_node)
        try:
            install.run(inst)
        finally:
            shutil.rmtree(install_dir)

    def test_simple(self):
        """Test whether install runs at all for a trivial package."""
        bento_info = """\
Name: foo

Library:
    Packages: foo, foo.bar
    Modules: fubar
"""
        self._test_run(bento_info)

    def test_simple_extension(self):
        """Test whether install runs at all for a trivial package."""
        bento_info = """\
Name: foo

Library:
    Packages: foo, foo.bar
    Modules: fubar
    Extension: foo
        Sources: src/foo.c
"""
        self._test_run(bento_info)
