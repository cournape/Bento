import os
import sys
import tempfile
import shutil

import os.path as op

import mock

from bento.compat.api.moves \
    import \
        unittest
from bento.core.node \
    import \
        create_base_nodes

if sys.platform == "darwin":
    import bento.commands.build_mpkg

from bentomakerlib.bentomaker \
    import \
        main

class TestMain(unittest.TestCase):
    def setUp(self):
        super(TestMain, self).setUp()

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
        super(TestMain, self).tearDown()

    # FIXME: stupid mock to reset global state between tests
    @mock.patch("bentomakerlib.bentomaker.__CACHED_PACKAGE", None)
    def test_no_bento(self):
        main([])

    @mock.patch("bentomakerlib.bentomaker.__CACHED_PACKAGE", None)
    def test_global_options_version(self):
        main(["--version"])

    @mock.patch("bentomakerlib.bentomaker.__CACHED_PACKAGE", None)
    def test_global_options_full_version(self):
        main(["--full-version"])

    @mock.patch("bentomakerlib.bentomaker.__CACHED_PACKAGE", None)
    def test_usage(self):
        main(["--help"])

    #@mock.patch("bentomakerlib.bentomaker.__CACHED_PACKAGE", None)
    #def test_help_non_existing_command(self):
    #    main(["help", "floupi"])

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

