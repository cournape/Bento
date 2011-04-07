import os
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
        prepare_configure, create_fake_package, create_fake_package_from_bento_info
from bento.commands.build \
    import \
        BuildCommand
from bento.commands.install \
    import \
        InstallCommand
from bento.commands.options \
    import \
        OptionsContext, Option

BENTO_INFO = """\
Name: foo

Library:
    Packages: foo, foo.bar
    Modules: fubar
"""

class TestBuildCommand(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.root = create_root_with_source_tree(self.d, os.path.join(self.d, "build"))

        self.old_dir = os.getcwd()
        os.chdir(self.d)

    def tearDown(self):
        os.chdir(self.old_dir)
        shutil.rmtree(self.d)

    def test_simple(self):
        root = self.root
        top_node = root.srcnode

        create_fake_package_from_bento_info(top_node, BENTO_INFO)
        conf, configure = prepare_configure(top_node, BENTO_INFO, ConfigureYakuContext)
        configure.run(conf)
        conf.store()

        build = BuildCommand()
        opts = OptionsContext()
        for o in BuildCommand.common_options:
            opts.add_option(o)

        bld = BuildYakuContext(build, [], opts, conf.pkg, top_node)
        build.run(bld)
        build.shutdown(bld)

        install = InstallCommand()
        opts = OptionsContext()
        for o in InstallCommand.common_options:
            opts.add_option(o)
        inst = CmdContext(install, [], opts, conf.pkg, top_node)
        install.run(inst)
