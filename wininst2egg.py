import os
import sys
import zipfile
import tempfile

import bento

if __name__ == "__main__":
    if len(sys.argv) < 2:
        WININST = "bento-0.0.3dev-py2.6.win32.exe"
    else:
        WININST = sys.argv[1]

    tmpdir = tempfile.mkdtemp()
    print tmpdir

    z = zipfile.ZipFile(WININST)
    try:
        #ipkg_info = z.read("SCRIPTS")
        z.extractall(path=tmpdir)
    finally:
        z.close()
