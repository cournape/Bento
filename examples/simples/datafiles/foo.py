import os
import shutil

from bento.commands.install \
    import \
        rollback_transaction, TransactionLog
from bento.installed_package_description \
    import \
        InstalledPkgDescription, iter_files

ipkg = InstalledPkgDescription.from_file("build/bento/ipkg.info")
prefix = os.path.join(os.getcwd(), "tmp")
ipkg.update_paths({"prefix": prefix, "eprefix": prefix})

#if os.path.exists(prefix):
#    shutil.rmtree(prefix)
#f = os.path.join(prefix, "share", "hello", "foo.src")
#os.makedirs(os.path.dirname(f))
#open(f, "w").write("")

os.remove("foo.log")
t = TransactionLog("foo.log")
try:
    for category, source, target in iter_files(ipkg.resolve_paths()):
        t.copy(source, target, category)
finally:
    t.close()

#rollback_transaction("foo.log")
