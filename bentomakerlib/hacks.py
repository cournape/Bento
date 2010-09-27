import os
try:
    from hashlib import md5
except ImportError:
    import md5
import cPickle

def _argv_checksum(argv):
    return md5(cPickle.dumps(argv)).hexdigest()

def _read_argv_checksum(cmd_name):
    fid = open("build/bento/argcheck.db", "rb")
    try:
        data = cPickle.load(fid)
        return data[cmd_name]
    finally:
        fid.close()

def _write_argv_checksum(checksum, cmd_name):
    if os.path.exists("build/bento/argcheck.db"):
        fid = open("build/bento/argcheck.db", "rb")
        try:
            data = cPickle.load(fid)
        finally:
            fid.close()
    else:
        data = {}

    data[cmd_name] = checksum
    fid = open("build/bento/argcheck.db", "wb")
    try:
        cPickle.dump(data, fid)
    finally:
        fid.close()
