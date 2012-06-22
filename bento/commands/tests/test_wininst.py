import os
import shutil
import tempfile
import zipfile

import os.path as op

import mock

import bento.commands.build_wininst

from bento.commands.build_wininst \
    import \
        create_wininst
from bento.compat.api.moves \
    import \
        unittest
from bento.core.node \
    import \
        create_base_nodes
from bento.installed_package_description \
    import \
        BuildManifest

class TestWininstInfo(unittest.TestCase):
    def setUp(self):
        self.old_dir = None
        self.tmpdir = None

        self.old_dir = os.getcwd()
        self.tmpdir = tempfile.mkdtemp()

        try:
            self.top_node, self.build_node, self.run_node = \
                    create_base_nodes(self.tmpdir, op.join(self.tmpdir, "build"))
            os.chdir(self.tmpdir)
        except:
            shutil.rmtree(self.tmpdir)
            raise

    def tearDown(self):
        os.chdir(self.old_dir)
        shutil.rmtree(self.tmpdir)

    @mock.patch("bento.commands.build_wininst.create_exe", mock.MagicMock())
    def test_simple(self):
        """This just tests whether create_wininst runs at all and produces a zip-file."""
        ipackage = BuildManifest({}, {"name": "foo", "version": "1.0"}, {})
        create_wininst(ipackage, self.build_node, self.build_node, wininst="foo.exe", output_dir="dist")
        arcname = bento.commands.build_wininst.create_exe.call_args[0][1]
        fp = zipfile.ZipFile(arcname)
        try:
            fp.namelist()
        finally:
            fp.close()
