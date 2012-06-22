import encodings
import os
import shutil
import tempfile
import mock

try:
    from hashlib import md5
except ImportError:
    from md5 import md5

import os.path as op
import distutils.msvccompiler

from bento._config \
    import \
        WININST_DIR
from bento.core.node \
    import \
        create_root_with_source_tree
from bento.testing.misc \
    import \
        create_simple_ipkg_args
from bento.commands.wininst_utils \
    import \
        get_inidata, create_exe, get_exe_bytes
from bento.installed_package_description \
    import \
        BuildManifest

from bento.compat.api import moves

class TestWininstUtils(moves.unittest.TestCase):
    def setUp(self):
        self.src_root = tempfile.mkdtemp()
        self.bld_root = op.join(self.src_root, "build")

        root = create_root_with_source_tree(self.src_root, self.bld_root)
        self.top_node = root.find_node(self.src_root)

    def tearDown(self):
        shutil.rmtree(self.top_node.abspath())

    def test_get_inidata_run(self):
        """Simply execute get_inidata."""
        # FIXME: do a real test here
        meta, sections, nodes = create_simple_ipkg_args(self.top_node)
        ipkg = BuildManifest(sections, meta, {})
        get_inidata(ipkg)

    @mock.patch('distutils.msvccompiler.get_build_version', lambda: 9.0)
    @mock.patch('encodings._cache', {"mbcs": encodings.search_function("ascii")})
    def test_create_exe(self):
        # FIXME: do a real test here
        meta, sections, nodes = create_simple_ipkg_args(self.top_node)
        ipkg = BuildManifest(sections, meta, {})

        fid, arcname = tempfile.mkstemp(prefix="zip")
        try:
            create_exe(ipkg, arcname, "some-name.exe")
        finally:
            os.close(fid)

class TestGetExeBytes(moves.unittest.TestCase):
    def _test_get_exe_bytes(self, version, exe_name):
        exe_name = op.join(WININST_DIR, exe_name)
        distutils.msvccompiler.get_build_version = lambda: version
        binary_header = get_exe_bytes()
        fid = open(exe_name, "rb")
        try:
            r_md5 = md5(fid.read())
            self.assertEqual(md5(binary_header).hexdigest(), r_md5.hexdigest())
        finally:
            fid.close()

    @mock.patch('distutils.msvccompiler.get_build_version', lambda: 9.0)
    def test_get_exe_bytes_9(self):
        self._test_get_exe_bytes(9.0, "wininst-9.0.exe")

    @mock.patch('distutils.msvccompiler.get_build_version', lambda: 9.0)
    def test_get_exe_bytes_8(self):
        self._test_get_exe_bytes(8.0, "wininst-8.0.exe")

    @mock.patch('distutils.msvccompiler.get_build_version', lambda: 7.1)
    def test_get_exe_bytes_7_1(self):
        self._test_get_exe_bytes(7.1, "wininst-7.1.exe")
