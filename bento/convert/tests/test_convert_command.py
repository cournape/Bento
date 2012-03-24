import os
import copy
import shutil
import tempfile

import os.path as op

import bento.convert.commands

from bento.commands.errors \
    import \
        UsageException
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
        ConvertCommand, DetectTypeCommand
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

def _run_convert_command(top_node, run_node, setup_py, bento_info, cmd_argv):
    setup_node = top_node.make_node("setup.py")
    setup_node.safe_write(setup_py)

    create_fake_package_from_bento_info(top_node, bento_info)
    package = PackageDescription.from_string(bento_info)

    cmd = ConvertCommand()
    opts = OptionsContext.from_command(cmd)

    context = CmdContext(None, cmd_argv, opts, package, run_node)
    cmd.run(context)
    cmd.shutdown(context)
    context.shutdown()

class CommonTestCase(unittest.TestCase):
    def setUp(self):
        super(CommonTestCase, self).setUp()
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

        super(CommonTestCase, self).tearDown()

class TestConvertCommand(SubprocessTestCase, CommonTestCase):
    def test_simple_package(self):
        bento_meta_data = bento_meta_data_template % bento_dummy_meta_data
        bento_info = """\
%s

ExtraSourceFiles:
    setup.py

Library:
    Packages:
        foo
""" % bento_meta_data

        setup_py = """\
from distutils.core import setup
setup(packages=["foo"], **%s)
""" % dummy_meta_data

        output = "foo.info"
        cmd_argv = ["--output=%s" % output, "-t", "distutils"]

        _run_convert_command(self.top_node, self.run_node, setup_py, bento_info, cmd_argv=cmd_argv)
        gen_bento = self.top_node.find_node(output)
        self.assertEqual(gen_bento.read(), bento_info)

    def test_package_data_distutils(self):
        bento_meta_data = bento_meta_data_template % bento_dummy_meta_data
        bento_info = """\
%s

ExtraSourceFiles:
    setup.py

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

        output = "foo.info"
        cmd_argv = ["--output=%s" % output, "-t", "distutils"]

        _run_convert_command(self.top_node, self.run_node, setup_py, bento_info, cmd_argv=cmd_argv)
        gen_bento = self.top_node.find_node(output)
        self.assertEqual(gen_bento.read(), bento_info)

class TestMockedConvertCommand(CommonTestCase):
    """Test the convert command UI."""
    def setUp(self):
        super(TestMockedConvertCommand, self).setUp()

        def dummy_convert(ctx, filename, setup_args, monkey_patch_mode, verbose, output, log, show_output):
            pass
        self.old_convert = bento.convert.commands.convert
        try:
            bento.convert.commands.convert = lambda *a: None
        except:
            bento.convert.commands.convert = self.old_convert

    def tearDown(self):
        bento.convert.commands.convert.convert = self.old_convert

        super(TestMockedConvertCommand, self).tearDown()

    def test_simple(self):
        bento_info = """\
Name: foo

Library:
    Packages:
        foo
"""

        setup_py = """\
from distutils.core import setup
setup(packages=["foo"], name="foo")
"""
        _run_convert_command(self.top_node, self.run_node, setup_py, bento_info, [])

    def test_help(self):
        bento_info = """\
Name: foo

Library:
    Packages:
        foo
"""

        setup_py = """\
from distutils.core import setup
setup(packages=["foo"], name="foo")
"""
        _run_convert_command(self.top_node, self.run_node, setup_py, bento_info, ["-h"])

    def test_not_overwritten(self):
        bento_info = """\
Name: foo

Library:
    Packages:
        foo
"""

        setup_py = """\
from distutils.core import setup
setup(packages=["foo"], name="foo")
"""
        self.top_node.make_node("bento.info").write("")
        self.assertRaises(UsageException,
                          lambda: _run_convert_command(self.top_node,
                              self.run_node, setup_py, bento_info,
                              ["--output=bento.info"]))

class TestMockedDetectTypeCommand(CommonTestCase):
    """Test the detect_type command UI."""
    def setUp(self):
        super(TestMockedDetectTypeCommand, self).setUp()

        self.old_whole_test = bento.convert.commands.whole_test
        try:
            bento.convert.commands.whole_test = lambda *a: None
        except:
            bento.convert.commands.whole_test = self.old_whole_test

    def tearDown(self):
        bento.convert.commands.convert.whole_test = self.old_whole_test

        super(TestMockedDetectTypeCommand, self).tearDown()

    def _run_command(self):
        setup_node = self.top_node.make_node("setup.py")
        setup_node.safe_write("")

        create_fake_package_from_bento_info(self.top_node, "")
        package = PackageDescription.from_string("")

        cmd = DetectTypeCommand()
        opts = OptionsContext.from_command(cmd)

        context = CmdContext(None, [], opts, package, self.run_node)
        cmd.run(context)
        cmd.shutdown(context)
        context.shutdown()

    def test_simple(self):
        self._run_command()
