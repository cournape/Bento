import sys
import os
import zipfile
import shutil

from bento.core \
    import \
        PackageMetadata
from bento.installed_package_description \
    import \
        InstalledPkgDescription
from bento.commands.build_wininst \
    import \
        create_wininst, wininst_filename
from bento.commands.script_utils \
    import \
        create_scripts

if __name__ == "__main__":
    import tempfile

    TMPDIR = tempfile.mkdtemp()
    try:
        EGG_PATH = sys.argv[1]

        zid = zipfile.ZipFile(EGG_PATH)
        try:
            zid.extractall(path=TMPDIR)
        finally:
            zid.close()
        ipkg = InstalledPkgDescription.from_egg(EGG_PATH)

        # Build executables
        bdir = os.path.join(TMPDIR, "SCRIPTS")
        os.makedirs(bdir)
        create_scripts(ipkg.executables, bdir)
        # XXX: use internal API
        for k in ipkg.files["executables"]:
            ipkg.files["executables"][k].source_dir = bdir

        meta = PackageMetadata.from_ipkg(ipkg)
        wininst = wininst_filename(meta.fullname)
        create_wininst(ipkg, src_root_dir=TMPDIR, wininst=wininst)
    finally:
        #shutil.rmtree(TMPDIR)
        pass
