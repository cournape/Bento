import os
import sys
import zipfile
import tempfile
import struct
import base64
import shutil

from cStringIO import StringIO

import bento
from bento.installed_package_description \
    import \
        InstalledPkgDescription
from bento.commands.build_egg \
    import \
        build_egg

def read_ipkg(wininst):
    # See eof_cdir size in archive.h of bdist_wininst sources
    eof_cdir_n = 22
    eof_cdir_tag = 0x06054b50

    meta_n = 12

    stat_info = os.stat(WININST)
    inst_size = stat_info.st_size

    with open(WININST, "rb") as fid:
        fid.seek(-eof_cdir_n, 2)
        s = fid.read(4)
        tag = struct.unpack("<l", s)[0]
        if not tag == eof_cdir_tag:
            raise ValueError("Unexpected bits")
        fid.read(2 * 4)
        s = fid.read(4)
        nBytesCDir = struct.unpack("<l", s)[0]
        s = fid.read(4)
        ofsCDir = struct.unpack("<l", s)[0]

        arc_start = inst_size - eof_cdir_n - nBytesCDir - ofsCDir
        ofs = arc_start - meta_n
        fid.seek(ofs, 0)
        s = fid.read(4)
        tag = struct.unpack("<l", s)[0]
        if not tag == 0x1234567B:
            raise ValueError("Unexpected bits")

        s = fid.read(4)
        uncomp_size = struct.unpack("<l", s)[0]

        s = fid.read(4)
        bitmap_size = struct.unpack("<l", s)[0]
        pexe_size = ofs - uncomp_size - bitmap_size

        fid.seek(pexe_size, 0)
        data = fid.read(uncomp_size)

        from ConfigParser import ConfigParser
        parser = ConfigParser()
        sdata = StringIO(data)

        def truncate_null(sdata):
            cur = sdata.tell()
            sdata.seek(0, 2)
            nbytes = sdata.tell()
            try:
                n = 10
                sdata.seek(-n, 2)
                null_ind = sdata.read().find("\0")
                sdata.truncate(nbytes - (n-null_ind))
            finally:
                sdata.seek(cur, 0)
        truncate_null(sdata)
        parser.readfp(sdata)
        raise ValueError("YO - fix wininst METADATA")
        ipkg_str = base64.b64decode(parser.get("IPKG_INFO", "value"))

        ipkg = InstalledPkgDescription.from_string(ipkg_str)
        return ipkg

if __name__ == "__main__":
    from bento.commands.wininst_utils import get_exe_bytes
    if len(sys.argv) < 2:
        WININST = "bento-0.0.3dev-py2.6.win32.exe"
    else:
        WININST = sys.argv[1]

    ipkg = read_ipkg(WININST)
    tmpdir = tempfile.mkdtemp()

    z = zipfile.ZipFile(WININST)
    try:
        z.extractall(path=tmpdir)
        build_egg(ipkg, source_root=os.path.join(tmpdir, "PURELIB"), path=".")
    finally:
        z.close()
        shutil.rmtree(tmpdir)
