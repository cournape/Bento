import os
import shutil
import tempfile

from bento.compat.api.moves \
    import \
        unittest

from bento.core.package \
    import \
        PackageDescription
from bento.core.node \
    import \
        create_root_with_source_tree
from bento.core.testing \
    import \
        create_fake_package_from_bento_info
from bento.commands.cmd_contexts \
    import \
        CmdContext
from bento.commands.options \
    import \
        OptionsContext
from bento.convert.commands \
    import \
        ConvertCommand

class TestConvertCommand(unittest.TestCase):
    def setUp(self):
        self.save = os.getcwd()
        self.d = tempfile.mkdtemp()
        os.chdir(self.d)
        try:
            self.root = create_root_with_source_tree(self.d, os.path.join(self.d, "build"))
            self.top_node = self.root._ctx.srcnode
            self.build_node = self.root._ctx.bldnode
            self.run_node = self.root.find_node(self.d)
        except Exception:
            os.chdir(self.save)
            raise

    def tearDown(self):
        os.chdir(self.save)
        shutil.rmtree(self.d)

    def test_simple_package(self):
        bento_info = """\
Name: foo
Version: 1.0
Summary: a few words
Url: http://example.com
DownloadUrl: http://example.com/download
Description: some more
    words
Author: John Doe
AuthorEmail: john@example.com
Maintainer: John Doe
MaintainerEmail: john@example.com
License: BSD
Platforms: UNIX

Library:
    Packages:
        foo
"""

        setup_py = """\
from distutils.core import setup
setup(name="foo",
      version="1.0",
      description="a few words",
      long_description="some more\\nwords",
      url="http://example.com",
      download_url="http://example.com/download",
      author="John Doe",
      maintainer="John Doe",
      author_email="john@example.com",
      maintainer_email="john@example.com",
      license="BSD",
      platforms=["UNIX"],
      packages=["foo"])
"""
        setup_node = self.top_node.make_node("setup.py")
        setup_node.safe_write(setup_py)

        create_fake_package_from_bento_info(self.top_node, bento_info)
        package = PackageDescription.from_string(bento_info)

        cmd = ConvertCommand()
        opts = OptionsContext.from_command(cmd)
        cmd_argv = ["--output=foo.info"]

        context = CmdContext(None, cmd_argv, opts, package, self.run_node)
        cmd.run(context)
        cmd.shutdown(context)
        context.shutdown()

        gen_bento = self.top_node.find_node("foo.info")
        self.assertEqual(gen_bento.read(), bento_info)
