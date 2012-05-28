import errno
import shutil

from bento.utils.utils \
    import \
        extract_exception
from bento.compat.api \
    import \
        rename as _rename

def rename(source, target):
    try:
        _rename(source, target)
    except OSError:
        e = extract_exception()
        if e.errno == errno.EXDEV:
            shutil.move(source, target)
        else:
            raise

