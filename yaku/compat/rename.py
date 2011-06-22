import os
import os.path
import random

from yaku.compat.py3k \
    import \
        get_exception

def rename(src, dst):
    "Atomic rename on windows."
    # This is taken from mercurial
    try:
        os.rename(src, dst)
    except OSError:
        err = get_exception()
        # If dst exists, rename will fail on windows, and we cannot
        # unlink an opened file. Instead, the destination is moved to
        # a temporary location if it already exists.

        def tempname(prefix):
            for i in range(5):
                fn = '%s-%08x' % (prefix, random.randint(0, 0xffffffff))
                if not os.path.exists(fn):
                    return fn
            raise IOError(errno.EEXIST, "No usable temporary filename found")

        temp = tempname(dst)
        os.rename(dst, temp)
        try:
            os.unlink(temp)
        except:
            # Some rude AV-scanners on Windows may cause the unlink to
            # fail. Not aborting here just leaks the temp file, whereas
            # aborting at this point may leave serious inconsistencies.
            # Ideally, we would notify the user here.
            pass
        os.rename(src, dst)
