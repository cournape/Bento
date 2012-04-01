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
                    _get_cmd_data_provider, CMD_DATA_DUMP

            cmd_data_db = self.build_node.find_node(CMD_DATA_DUMP)
            q.put(_get_cmd_data_provider(cmd_data_db).get_argv("configure"))

        q = multiprocessing.Queue()
        p = multiprocessing.Process(target=check_cmd_data, args=(q,))
        p.start()
        self.assertEqual(q.get(), ["--prefix=/fubar"])
        p.join()
