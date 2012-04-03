import os
import os.path as op
import shutil
import tempfile

from bento.compat.api.moves \
    import \
        unittest

from bento.core.node \
    import \
        create_root_with_source_tree
from bento.core.testing \
    import \
        create_fake_package_from_bento_infos
from bento.commands.command_contexts \
    import \
        ConfigureContext
from bento.commands.hooks \
    import \
        create_hook_module, find_pre_hooks, find_post_hooks

from bento.commands.tests.utils \
    import \
        prepare_configure

class TestHooks(unittest.TestCase):
    def setUp(self):
        self.old_cwd = os.getcwd()
        self.new_cwd = tempfile.mkdtemp()
        try:
            os.chdir(self.new_cwd)
            try:
                root = create_root_with_source_tree(self.new_cwd,
                        op.join(self.new_cwd, "build"))
                self.top_node = root._ctx.srcnode
                self.build_node = root._ctx.bldnode
            except:
                os.chdir(self.old_cwd)
                raise
        except:
            shutil.rmtree(self.new_cwd)
            raise

    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.new_cwd)

    def test_simple(self):
        bscript = """\
from bento.commands import hooks

PRE = False
POST = False

@hooks.pre_configure
def pre_configure(ctx):
    global PRE
    PRE = True

@hooks.post_configure
def post_configure(ctx):
    global POST
    POST = True
"""

        bento = """\
Name: foo
Version: 1.0

HookFile: bscript
"""

        create_fake_package_from_bento_infos(self.top_node, {"bento.info": bento},
                {"bscript": bscript})

        conf, configure = prepare_configure(self.top_node, bento,
                ConfigureContext)
        bscript = self.top_node.search("bscript")
        m = create_hook_module(bscript.abspath())
        self.assertEqual(len(find_pre_hooks([m], "configure")), 1)
        self.assertEqual(len(find_post_hooks([m], "configure")), 1)
