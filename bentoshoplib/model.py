import os
import sqlite3

from bento.core.utils \
    import \
        ensure_dir
from bentoshoplib._config \
    import \
        BENTO_DB

# Minimal features set:
#   - list installed packages with version
#   - each package: name, version, author, description, summary
PACKAGE_META_TABLE = """\
CREATE TABLE PACKAGE_METADATA (
    id INTEGER,
    name TEXT,
    version TEXT,
    author TEXT,
    summary TEXT,
    description TEXT,
    PRIMARY KEY (id)
)
"""

def init_scheme(filename=BENTO_DB, force=False):
    if os.path.exists(filename):
        if force:
            print "Overwriting db..."
            os.remove(filename)
        else:
            raise ValueError("db %s already exists" % filename)
    else:
        ensure_dir(filename)
    cx = sqlite3.connect(filename)
    c = cx.cursor()
    try:
        c.execute(PACKAGE_META_TABLE)
        cx.commit()
    finally:
        c.close()

class PackageIndex(object):
    def __init__(self):
        self._dbfile = BENTO_DB
        if not os.path.exists(self._dbfile):
            raise IOError("Database %s not found" % self._dbfile)

        self._cx = sqlite3.connect(self._dbfile)

    def add_package(self, package_metadata):
        name = package_metadata.name
        version = package_metadata.version
        c = self._cx.cursor()
        try:
            c.execute("SELECT id FROM PACKAGE_METADATA WHERE name = ?", (name,))
            if c.fetchone() is not None:
                raise ValueError("Package %s already registered !" % name)
            else:
                c.execute("INSERT INTO PACKAGE_METADATA (name, version) VALUES (?,?)", (name, version))
            self._cx.commit()
        finally:
            c.close()

    def list_packages(self):
        c = self._cx.cursor()
        try:
            c.execute("SELECT DISTINCT(name) FROM PACKAGE_METADATA")
            return [row[0] for row in c.fetchall()]
        finally:
            c.close()
