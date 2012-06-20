import os
import shutil
import tempfile

import mock

import bento.core.testing

from bento.commands.command_contexts \
    import \
        ContextWithBuildDirectory
from bento.commands.options \
    import \
        OptionsContext
from bento.commands.sphinx_command \
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

def has_sphinx():
    try:
        import sphinx
        return True
    except ImportError:
        return False

class TestSphinx(unittest.TestCase):
    def setUp(self):
        self.save = os.getcwd()
        self.d = tempfile.mkdtemp()
        os.chdir(self.d)
        try:
            self.top_node, self.build_node, self.run_node = create_base_nodes()
        except Exception:
            os.chdir(self.save)
            raise

    def tearDown(self):
        os.chdir(self.save)
        shutil.rmtree(self.d)

    @bento.core.testing.skip_if(not has_sphinx(), "sphinx not available, skipping sphinx command test(s)")
    def test_simple(self):
        n = self.top_node.make_node("doc/conf.py")
        n.parent.mkdir()
        n.write("")

        n = self.top_node.make_node("doc/contents.rst")
        n.write("")

        bento_info = "Name: foo"
        package = PackageDescription.from_string(bento_info)

        sphinx = SphinxCommand()
        opts = OptionsContext.from_command(sphinx)
        context = ContextWithBuildDirectory(None, [], opts, package, self.run_node)

        run_command_in_context(context, sphinx)
