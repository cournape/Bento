"""
Cache version 1

db["version"] : version number
db["magic"] : "BENTOMAGIC"
db["bento_checkums"] : pickled dictionary {filename: checksum(filename)} for
                       each bento.info (including subentos)
db["package_description"] : pickled PackageDescription instance
db["user_flags"] : pickled user_flags dict
"""
import os
import copy
import anydbm
import cPickle
try:
    from hashlib import md5
except ImportError:
    import md5

from bento._config \
    import \
        DB_FILE
from bento.core.package \
    import \
        parse_to_pkg_kw, PackageDescription
from bento.core.utils \
    import \
        ensure_dir

from cPickle import load, dump, loads, dumps

class CachedPackage(object):
    __version__ = "1"
    __magic__ = "BENTOMAGIC"

    def __init__(self, db_location=DB_FILE):
        self._location = db_location
        self._first_time = False
        if not os.path.exists(db_location):
            ensure_dir(db_location)
#            self.db = anydbm.open(db_location, "c")
            self.db = {}
            self.db["magic"] = CachedPackage.__magic__
            self.db["version"] = CachedPackage.__version__
            self._first_time = True
        else:
            #self.db = anydbm.open(db_location, "c")
            self.db = load(open(db_location))
            try:
                magic = self.db["magic"]
                if not magic == self.__magic__:
                    raise ValueError("Db is not a cached package db !")
            except KeyError:
                raise ValueError("Db is not a cached package db !")

            version = self.db["version"]
            if version != self.__version__:
                raise ValueError("Invalid db version")

    def has_changed(self):
        if self.db.has_key("bentos_checksums"):
            r_checksums = cPickle.loads(self.db["bentos_checksums"])
            for f in r_checksums:
                checksum = md5(open(f).read()).hexdigest()
                if checksum != r_checksums[f]:
                    return True
            return False
        else:
            raise ValueError("Incomplete db !")

    def get_package(self, filename, user_flags=None):
        if self._first_time:
            print "CACHE FIRST TIME"
            return _create_package_nocached(filename, user_flags, self.db)
        else:
            if self.has_changed():
                print "CACHE HAS CHANGED"
                return _create_package_nocached(filename, user_flags, self.db)
            else:
                r_user_flags = cPickle.loads(self.db["user_flags"])
                if user_flags is None:
                    # FIXME: this case is wrong
                    print "CACHE NOT USER FLAGS"
                    return cPickle.loads(self.db["package_description"])
                elif r_user_flags != user_flags:
                    print "CACHE != USER FLAGS"
                    return _create_package_nocached(filename, user_flags, db)
                else:
                    print "CACHE GOOD FLAGS"
                    return cPickle.loads(self.db["package_description"])

    def close(self):
        #self.db.close()
        f = open(self._location, "wb")
        try:
            dump(self.db, f)
        finally:
            f.close()

def _create_package_nocached(filename, user_flags, db):
    info_file = open(filename, 'r')
    try:
        data = info_file.read()
        kw, files = parse_to_pkg_kw(data, user_flags, filename)

        pkg = PackageDescription(**kw)
        # FIXME: find a better way to automatically include the
        # bento.info file
        pkg.extra_source_files.append(filename)

        files.append(filename)
        checksums = [md5(open(f).read()).hexdigest() for f in files]
        db["bentos_checksums"] = cPickle.dumps(dict(zip(files, checksums)))
        db["package_description"] = cPickle.dumps(pkg)
        db["user_flags"] = cPickle.dumps(user_flags)

        return pkg
    finally:
        info_file.close()

#def create_package_description(filename, user_flags=None):
#    if not os.path.exists(os.path.dirname(DB_FILE)):
#        os.makedirs(os.path.dirname(DB_FILE))
#
#    db = anydbm.open(DB_FILE, "c")
#    try:
#        if db.has_key("bentos_checksums"):
#            r_checksums = cPickle.loads(db["bentos_checksums"])
#            r_user_flags = cPickle.loads(db["user_flags"])
#            if user_flags is None:
#                user_flags = copy.deepcopy(r_user_flags)
#
#            def has_changed():
#                if r_user_flags != user_flags:
#                    return True
#                for f in r_checksums:
#                    checksum = md5(open(f).read()).hexdigest()
#                    if checksum != r_checksums[f]:
#                        return True
#                return False
#            if has_changed():
#                print "HAS CHANGED"
#                return _create_package_nocached(filename, user_flags, db)
#            else:
#                print "HAS NOT CHANGED"
#                return cPickle.loads(db["package_description"])
#        else:
#            print "FIRST TIME"
#            return _create_package_nocached(filename, user_flags, db)
#    finally:
#        db.close()
#
