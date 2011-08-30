import os
import shutil
import unittest
import tempfile

from bento.core \
    import \
        PackageDescription, PackageOptions
from bento.core.node \
    import \
        create_root_with_source_tree
from bento.commands.hooks \
    import \
        get_pre_hooks, create_hook_module, get_post_hooks
from bento.commands.options \
    import \
        OptionsContext
from bento.commands.context \
    import \
        ConfigureYakuContext, BuildYakuContext
from bento.commands.build \
    import \
        BuildCommand

from bento.core.testing \
    import \
        create_fake_package_from_bento_infos
from bento.commands.tests.utils \
    import \
        prepare_configure

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

    def test_simple(self):
        root = self.root
        top_node = self.top_node
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
    Modules: fubar
    Extension: _foo
        Sources: foo.c
"""

        bento_info3 = """\
Library:
    Modules: foufoufou
    Packages: sub2
"""
        bentos = {"bento.info": bento_info, os.path.join("bar", "bento.info"): bento_info2,
                  os.path.join("bar", "foo", "bento.info"): bento_info3}
        create_fake_package_from_bento_infos(run_node, bentos)

        conf, configure = prepare_configure(run_node, bento_info, ConfigureYakuContext)
        configure.run(conf)
        conf.shutdown()

        build = BuildCommand()
        opts = OptionsContext.from_command(build)

        cmd_argv = []
        bld = BuildYakuContext(cmd_argv, opts, conf.pkg, run_node)
        build.run(bld)

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
    Modules: fubar
"""

        bscript = """\
from bento.commands import hooks
@hooks.pre_configure
def configure(ctx):
    py_modules = ctx.local_pkg.py_modules
    ctx.local_node.make_node("test").write(str(py_modules))
"""
        bentos = {"bento.info": bento_info, os.path.join("bar", "bento.info"): bento_info2}
        bscripts = {os.path.join("bar", "bscript"): bscript}
        create_fake_package_from_bento_infos(top_node, bentos, bscripts)

        conf, configure = prepare_configure(self.run_node, bento_info, ConfigureYakuContext)

        hook = top_node.search("bar/bscript")
        m = create_hook_module(hook.abspath())
        for hook, local_dir, help_bypass in get_pre_hooks("configure"):
            conf.pre_recurse(root.find_dir(local_dir))
            try:
                hook(conf)
            finally:
                conf.post_recurse()

        test = top_node.search("bar/test")
        if test:
            self.failUnlessEqual(test.read(), "['fubar']")
        else:
            self.fail("test dummy not found")
