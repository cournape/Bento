"""
Cache version 1

db["version"] : version number
db["magic"]   : "BENTOMAGIC"
db["bento_checkums"] : pickled dictionary {filename: checksum(filename)} for
                       each bento.info (including subentos)
db["package_description"] : pickled PackageDescription instance
db["user_flags"] : pickled user_flags dict
db["parsed_dict"]: pickled raw parsed dictionary (as returned by
                   raw_parse, before having been seen by the visitor)
"""
import os
import sys
if sys.version_info[0] < 3:
    import cPickle as pickle
else:
    import pickle

try:
    from hashlib import md5
except ImportError:
    from md5 import md5
import warnings

from bento.core.parser.api \
    import \
        raw_parse
from bento.core.package \
    import \
        raw_to_pkg_kw, PackageDescription
from bento.core.options \
    import \
        raw_to_options_kw, PackageOptions
from bento.core.utils \
    import \
        ensure_dir, safe_write, extract_exception

class CachedPackage(object):
    def __init__(self, db_node):
        self._db_location = db_node

    def get_package(self, bento_info, user_flags=None):
        cache = _CachedPackageImpl(self._db_location.abspath())
        try:
            return cache.get_package(bento_info, user_flags)
        finally:
            cache.close()

    def get_options(self, bento_info):
        cache = _CachedPackageImpl(self._db_location.abspath())
        try:
            return cache.get_options(bento_info)
        finally:
            cache.close()

class _CachedPackageImpl(object):
    __version__ = "2"
    __magic__ = "CACHED_PACKAGE_BENTOMAGIC"

    def _has_valid_magic(self, db):
        try:
            magic = db["magic"]
            if not magic == self.__magic__:
                return False
            else:
                return True
        except KeyError:
            return False

    def _reset(self):
        self.db = {}
        self.db["magic"] = self.__magic__
        self.db["version"] = self.__version__
        self._first_time = True

    def _load_existing_cache(self, db_location):
        fid = open(db_location, "rb")
        try:
            db = pickle.load(fid)
            if not self._has_valid_magic(db):
                warnings.warn("Resetting invalid cached db")
                self._reset()
        finally:
            fid.close()

        version = db["version"]
        if version != self.__version__:
            warnings.warn("Resetting invalid version of cached db")
            self._reset()

        return db

    def __init__(self, db_location):
        self._location = db_location
        self._first_time = False
        if not os.path.exists(db_location):
            ensure_dir(db_location)
            self._reset()
        else:
            try:
                self.db = self._load_existing_cache(db_location)
            except Exception:
                e = extract_exception()
                warnings.warn("Resetting invalid cached db: (reason: %r)" % e)
                self._reset()

    def _has_invalidated_cache(self):
        if "bentos_checksums" in self.db:
            r_checksums = pickle.loads(self.db["bentos_checksums"])
            for f in r_checksums:
                checksum = md5(open(f, "rb").read()).hexdigest()
                if checksum != r_checksums[f]:
                    return True
            return False
        else:
            return True

    def get_package(self, bento_info, user_flags=None):
        try:
            return self._get_package(bento_info, user_flags)
        except Exception:
            e = extract_exception()
            warnings.warn("Resetting invalid cache (error was %r)" % e)
            self._reset()
            return self._get_package(bento_info, user_flags)

    def _get_package(self, bento_info, user_flags=None):
        if self._first_time:
            self._first_time = False
            return _create_package_nocached(bento_info, user_flags, self.db)
        else:
            if self._has_invalidated_cache():
                return _create_package_nocached(bento_info, user_flags, self.db)
            else:
                r_user_flags = pickle.loads(self.db["user_flags"])
                if user_flags is None:
                    # FIXME: this case is wrong
                    return pickle.loads(self.db["package_description"])
                elif r_user_flags != user_flags:
                    return _create_package_nocached(bento_info, user_flags, self.db)
                else:
                    raw = pickle.loads(self.db["parsed_dict"])
                    pkg, files = _raw_to_pkg(raw, user_flags, bento_info)
                    return pkg

    def get_options(self, bento_info):
        try:
            return self._get_options(bento_info)
        except Exception:
            e = extract_exception()
            warnings.warn("Resetting invalid cache (error was %r)" % e)
            self._reset()
            return self._get_options(bento_info)

    def _get_options(self, bento_info):
        if self._first_time:
            self._first_time = False
            return _create_options_nocached(bento_info, {}, self.db)
        else:
            if self._has_invalidated_cache():
                return _create_options_nocached(bento_info, {}, self.db)
            else:
                raw = pickle.loads(self.db["parsed_dict"])
                return _raw_to_options(raw)

    def close(self):
        safe_write(self._location, lambda fd: pickle.dump(self.db, fd))

def _create_package_nocached(bento_info, user_flags, db):
    pkg, options = _create_objects_no_cached(bento_info, user_flags, db)
    return pkg

def _create_options_nocached(bento_info, user_flags, db):
    pkg, options = _create_objects_no_cached(bento_info, user_flags, db)
    return options

def _raw_to_options(raw):
    kw = raw_to_options_kw(raw)
    return PackageOptions(**kw)

def _raw_to_pkg(raw, user_flags, bento_info):
    kw, files = raw_to_pkg_kw(raw, user_flags, bento_info)
    pkg = PackageDescription(**kw)
    return pkg, files

def _create_objects_no_cached(bento_info, user_flags, db):
    d = os.path.dirname(bento_info.abspath())
    info_file = open(bento_info.abspath(), 'r')
    try:
        data = info_file.read()
        raw = raw_parse(data, bento_info.abspath())

        pkg, files = _raw_to_pkg(raw, user_flags, bento_info)
        files = [os.path.join(d, f) for f in files]
        options = _raw_to_options(raw)

        checksums = [md5(open(f, "rb").read()).hexdigest() for f in files]
        db["bentos_checksums"] = pickle.dumps(dict(zip(files, checksums)))
        db["package_description"] = pickle.dumps(pkg)
        db["user_flags"] = pickle.dumps(user_flags)
        db["parsed_dict"] = pickle.dumps(raw)

        return pkg, options
    finally:
        info_file.close()
