import os
import copy
import shutil
import tempfile

import os.path as op

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
from bento.misc.testing \
    import \
        SubprocessTestCase

dummy_meta_data = dict(
        name="foo",
        version="1.0",
        description="a few words",
        long_description="some more words",
        url="http://example.com",
        download_url="http://example.com/download",
        author="John Doe",
        maintainer="John Doe",
        author_email="john@example.com",
        maintainer_email="john@example.com",
        license="BSD",
        platforms=["UNIX"],
)

bento_dummy_meta_data = copy.copy(dummy_meta_data)
bento_dummy_meta_data["platforms"] = ",".join(bento_dummy_meta_data["platforms"])

bento_meta_data_template = """\
Name: %(name)s
Version: %(version)s
Summary: %(description)s
Url: %(url)s
DownloadUrl: %(download_url)s
Description: %(long_description)s
Author: %(author)s
AuthorEmail: %(author_email)s
Maintainer: %(maintainer)s
MaintainerEmail: %(maintainer_email)s
License: %(license)s
Platforms: %(platforms)s"""

class TestConvertCommand(SubprocessTestCase):
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

    def _compare_bentos(self, setup_py, bento_info):
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

    def test_simple_package(self):
        bento_meta_data = bento_meta_data_template % bento_dummy_meta_data
        bento_info = """\
%s

Library:
    Packages:
        foo
""" % bento_meta_data

        setup_py = """\
from distutils.core import setup
setup(packages=["foo"], **%s)
""" % dummy_meta_data
        self._compare_bentos(setup_py, bento_info)

    def test_package_data_distutils(self):
        bento_meta_data = bento_meta_data_template % bento_dummy_meta_data
        bento_info = """\
%s

DataFiles: foo_data
    SourceDir: foo
    TargetDir: $sitedir/foo
    Files:
        info.txt

Library:
    Packages:
        foo
""" % bento_meta_data

        setup_py = """\
from distutils.core import setup
setup(packages=["foo"], package_data={"foo": ["*txt"]}, **%s)
""" % dummy_meta_data

        data_node = self.top_node.make_node(op.join("foo", "info.txt"))
        data_node.parent.mkdir()
        data_node.write("")

        self._compare_bentos(setup_py, bento_info)
