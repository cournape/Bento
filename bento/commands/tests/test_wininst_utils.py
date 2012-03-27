import os
import shutil
import tempfile

try:
    from hashlib import md5
except ImportError:
    from md5 import md5

import os.path as op

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
        InstalledPkgDescription

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
        ipkg = InstalledPkgDescription(sections, meta, {})
        get_inidata(ipkg)

    def test_create_exe(self):
        # FIXME: do a real test here
        meta, sections, nodes = create_simple_ipkg_args(self.top_node)
        ipkg = InstalledPkgDescription(sections, meta, {})

        import distutils.msvccompiler
        old_get_build_version = distutils.msvccompiler.get_build_version
        try:
            distutils.msvccompiler.get_build_version = lambda: 9.0
            fid, arcname = tempfile.mkstemp(prefix="zip")
            try:
                create_exe(ipkg, arcname, "some-name.exe")
            finally:
                os.close(fid)
        finally:
            distutils.msvccompiler.get_build_version = old_get_build_version

class TestGetExeBytes(moves.unittest.TestCase):
    def test_get_exe_bytes(self):
        import distutils.msvccompiler
        old_get_build_version = distutils.msvccompiler.get_build_version
        try:
            for version, exe_name in zip((9.0, 8.0, 7.1),
                    ("wininst-9.0.exe", "wininst-8.0.exe", "wininst-7.1.exe")):
                exe_name = op.join(WININST_DIR, exe_name)
                distutils.msvccompiler.get_build_version = lambda: version
                binary_header = get_exe_bytes()
                fid = open(exe_name, "rb")
                try:
                    r_md5 = md5(fid.read())
                    self.assertEqual(md5(binary_header).hexdigest(), r_md5.hexdigest())
                finally:
                    fid.close()
        finally:
            distutils.msvccompiler.get_build_version = old_get_build_version
