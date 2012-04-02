import os
import sys
import tempfile
import shutil

import os.path as op

import multiprocessing
import mock

from bento.compat.api.moves \
    import \
        unittest
from bento.core.node \
    import \
        create_base_nodes

# FIXME: nose is broken - needed to make it happy
if sys.platform == "darwin":
    import bento.commands.build_mpkg
# FIXME: nose is broken - needed to make it happy
import bento.commands.build_yaku
# FIXME: nose is broken - needed to make it happy
from bento.compat.dist \
    import \
        DistributionMetadata

from bento.commands.errors \
    import \
        UsageException

from bentomakerlib.bentomaker \
    import \
        main, noexc_main

class Common(unittest.TestCase):
    def setUp(self):
        super(Common, self).setUp()

        self.d = tempfile.mkdtemp()
        self.old = os.getcwd()

        try:
            os.chdir(self.d)
            self.top_node, self.build_node, self.run_node = create_base_nodes(self.d, op.join(self.d, "build"))
        except:
            os.chdir(self.old)
            shutil.rmtree(self.d)

    def tearDown(self):
        os.chdir(self.old)
        shutil.rmtree(self.d)
        super(Common, self).tearDown()

class TestSpecialCommands(Common):
    # FIXME: stupid mock to reset global state between tests
    @mock.patch("bentomakerlib.bentomaker.__CACHED_PACKAGE", None)
    def test_help_globals(self):
        main(["help", "globals"])

    @mock.patch("bentomakerlib.bentomaker.__CACHED_PACKAGE", None)
    def test_help_commands(self):
        main(["help", "commands"])

    @mock.patch("bentomakerlib.bentomaker.__CACHED_PACKAGE", None)
    def test_global_options_version(self):
        main(["--version"])

    @mock.patch("bentomakerlib.bentomaker.__CACHED_PACKAGE", None)
    def test_global_options_full_version(self):
        main(["--full-version"])

    @mock.patch("bentomakerlib.bentomaker.__CACHED_PACKAGE", None)
    def test_usage(self):
        main(["--help"])


class TestMain(Common):
    @mock.patch("bentomakerlib.bentomaker.__CACHED_PACKAGE", None)
    def test_no_bento(self):
        main([])

    @mock.patch("bentomakerlib.bentomaker.__CACHED_PACKAGE", None)
    def test_help_non_existing_command(self):
        self.assertRaises(UsageException, lambda: main(["help", "floupi"]))

    @mock.patch("bentomakerlib.bentomaker.__CACHED_PACKAGE", None)
    def test_configure_help(self):
        bento_info = """\
Name: foo
"""
        self.top_node.make_node("bento.info").write(bento_info)
        main(["configure", "--help"])

    @mock.patch("bentomakerlib.bentomaker.__CACHED_PACKAGE", None)
    def test_help_command(self):
        bento_info = """\
Name: foo
"""
        self.top_node.make_node("bento.info").write(bento_info)
        main(["help", "configure"])

    @mock.patch("bentomakerlib.bentomaker.__CACHED_PACKAGE", None)
    def test_configure(self):
        bento_info = """\
Name: foo
"""
        self.top_node.make_node("bento.info").write(bento_info)
        main(["configure"])

class TestMainCommands(Common):
    def setUp(self):
        super(TestMainCommands, self).setUp()

        bento_info = """\
Name: foo
"""
        self.top_node.make_node("bento.info").write(bento_info)

    def tearDown(self):
        super(TestMainCommands, self).tearDown()

    @mock.patch("bentomakerlib.bentomaker.__CACHED_PACKAGE", None)
    def test_configure(self):
        main(["configure"])

    @mock.patch("bentomakerlib.bentomaker.__CACHED_PACKAGE", None)
    def test_build(self):
        main(["build"])

    @mock.patch("bentomakerlib.bentomaker.__CACHED_PACKAGE", None)
    def test_install(self):
        main(["install"])

    @mock.patch("bentomakerlib.bentomaker.__CACHED_PACKAGE", None)
    def test_sdist(self):
        main(["sdist"])

    @mock.patch("bentomakerlib.bentomaker.__CACHED_PACKAGE", None)
    def test_build_egg(self):
        main(["build_egg"])

    @mock.patch("bentomakerlib.bentomaker.__CACHED_PACKAGE", None)
    @unittest.skipIf(sys.platform != "win32", "wininst is win32-only test")
    def test_wininst(self):
        main(["build_wininst"])

    @mock.patch("bentomakerlib.bentomaker.__CACHED_PACKAGE", None)
    @unittest.skipIf(sys.platform != "darwin", "mpkg is darwin-only test")
    def test_mpkg(self):
        main(["build_mpkg"])

class TestConvertCommand(Common):
    @mock.patch("bentomakerlib.bentomaker.__CACHED_PACKAGE", None)
    def test_convert(self):
        self.top_node.make_node("setup.py").write("""\
from distutils.core import setup

setup(name="foo")
""")
        main(["convert"])
        n = self.top_node.find_node("bento.info")
        r_bento = """\
Name: foo
Version: 0.0.0
Summary: UNKNOWN
Url: UNKNOWN
DownloadUrl: UNKNOWN
Description: UNKNOWN
Author: UNKNOWN
AuthorEmail: UNKNOWN
Maintainer: UNKNOWN
MaintainerEmail: UNKNOWN
License: UNKNOWN
Platforms: UNKNOWN

ExtraSourceFiles:
    setup.py
"""
        self.assertEqual(n.read(), r_bento)

class TestRunningEnvironment(Common):
    def test_in_sub_directory(self):
        bento_info = """\
Name: foo
"""
        self.top_node.make_node("bento.info").write(bento_info)

        subdir_node = self.top_node.make_node("subdir")
        subdir_node.mkdir()

        try:
            os.chdir(subdir_node.abspath())
            self.assertRaises(UsageException, lambda: main(["--bento-info=../bento.info", "configure"]))
        finally:
            os.chdir(self.top_node.abspath())

class TestCommandData(Common):
    def test_simple(self):
        # We use subprocesses to emulate how bentomaker would run itself - this
        # is more of a functional test than a unit test.
        bento_info = """\
Name: foo
"""
        self.top_node.make_node("bento.info").write(bento_info)

        p = multiprocessing.Process(target=noexc_main, args=(['configure', '--prefix=/fubar'],))
        p.start()
        p.join()

        def check_cmd_data(q):
            from bentomakerlib.bentomaker \
                import \
                    CommandDataProvider, CMD_DATA_DUMP

            cmd_data_db = self.build_node.find_node(CMD_DATA_DUMP)
            if cmd_data_db is None:
                raise IOError()
            cmd_data_store = CommandDataProvider.from_file(cmd_data_db.abspath())
            q.put(cmd_data_store.get_argv("configure"))

        q = multiprocessing.Queue()
        p = multiprocessing.Process(target=check_cmd_data, args=(q,))
        p.start()
        self.assertEqual(q.get(timeout=1), ["--prefix=/fubar"])
        p.join()

    def test_flags(self):
        """Test that flag value specified on the command line are correctly
        stored between run."""
        # We use subprocesses to emulate how bentomaker would run itself - this
        # is more of a functional test than a unit test.
        bento_info = """\
Name: foo

Flag: debug
    Description: debug flag
    Default: true

HookFile: bscript

Library:
    if flag(debug):
        Modules: foo
    else:
        Modules: bar
"""
        self.top_node.make_node("bento.info").write(bento_info)
        self.top_node.make_node("bscript").write("""\
import sys
from bento.commands import hooks

@hooks.pre_build
def pre_build(context):
    if not context.pkg.py_modules == ['bar']:
        sys.exit(57)
""")
        self.top_node.make_node("foo.py").write("")
        self.top_node.make_node("bar.py").write("")

        p = multiprocessing.Process(target=main, args=(['configure', '--debug=false'],))
        p.start()
        p.join()

        p = multiprocessing.Process(target=main, args=(['build'],))
        p.start()
        p.join()

        self.assertEqual(p.exitcode, 0)
