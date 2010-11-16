import os
import sys
import shutil
import zipfile

from bento.installed_package_description \
    import \
        InstalledPkgDescription, iter_files
from bento.core.utils import \
    subst_vars
from bento.commands.install \
    import \
        copy_installer

EGG = os.path.join("dist", "hello-1.0-py2.6.egg")

ipkg = InstalledPkgDescription.from_egg(EGG)
# egg scheme
ipkg.update_paths({"prefix": ".", "eprefix": ".", "sitedir": "."})

if os.path.exists("tmpextract"):
    shutil.rmtree("tmpextract")
os.makedirs("tmpextract")

zid = zipfile.ZipFile(EGG)
try:
    for type, sections in ipkg.files.items():
        for name, section in sections.items():
            target_dir = ipkg.resolve_path(section.target_dir)
            section.source_dir = os.path.join("tmpextract", target_dir)
            for f, g in section.files:
                g = os.path.join(target_dir, f)
                g = os.path.normpath(g)
                zid.extract(g, "tmpextract")
    ipkg.write("ipkg.info")
finally:
    zid.close()

ipkg = InstalledPkgDescription.from_file("ipkg.info")
# Reset paths
from bento.core.platforms.sysconfig import get_scheme
ipkg.update_paths(get_scheme(sys.platform)[0])
tmp = os.path.join(os.getcwd(), "tmp")
ipkg.update_paths({"prefix": tmp, "eprefix": tmp})

for category, source, target in iter_files(ipkg.resolve_paths()):
    copy_installer(source, target, category)
    #print "%s -> %s" % (source, target)
ipkg.write("installed.info")
