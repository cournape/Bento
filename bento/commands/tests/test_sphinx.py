import os
import shutil
import tempfile

import mock

from bento.commands.command_contexts \
    import \
        ContextWithBuildDirectory
from bento.commands.options \
    import \
        OptionsContext
from bento.commands.sphinx \
    import \
        SphinxCommand
from bento.commands.wrapper_utils \
    import \
        run_command_in_context
from bento.compat.api.moves \
    import \
        unittest
from bento.core.package \
    import \
        PackageDescription
from bento.core.node \
    import \
        create_base_nodes

class FakePopen(object):
    def __init__(self, *a, **kw):
        self.returncode = -1
    def wait(self):
        self.returncode = 0

class TestSphinx(unittest.TestCase):
    def setUp(self):
        self.save = os.getcwd()
        self.d = tempfile.mkdtemp()
        os.chdir(self.d)
        try:
            self.top_node, self.build_node, self.run_node = \
                    create_base_nodes(self.d, os.path.join(self.d, "build"))
        except Exception:
            os.chdir(self.save)
            raise

    def tearDown(self):
        os.chdir(self.save)
        shutil.rmtree(self.d)

    @mock.patch("bento.commands.sphinx.subprocess.Popen", FakePopen)
    def test_simple(self):
        self.top_node.make_node("doc").mkdir()

        bento_info = "Name: foo"
        package = PackageDescription.from_string(bento_info)

        sphinx = SphinxCommand()
        opts = OptionsContext.from_command(sphinx)
        context = ContextWithBuildDirectory(None, [], opts, package, self.run_node)

        run_command_in_context(context, sphinx)
