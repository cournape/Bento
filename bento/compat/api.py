import os
import sys

if os.name == "posix":
    from bento.compat.posix_path \
        import \
            relpath
    rename = os.rename
elif os.name == "nt":
    from bento.compat.nt_path \
        import \
            relpath
    from bento.compat.rename \
        import \
            rename
else:
    raise ImportError("relpath implementation for os %s not included" \
                      % os.name)

try:
    from subprocess \
        import \
            check_call, CalledProcessError
except ImportError:
    from bento.compat._subprocess \
        import \
            check_call, CalledProcessError

if sys.version_info < (2, 6, 0):
    # zipfile for python < 2.6 has some issues with filename encoding, use or
    # own copy
    from bento.compat._zipfile \
        import \
            ZipFile, ZIP_DEFLATED
else:
    from zipfile \
        import \
            ZipFile, ZIP_DEFLATED

if sys.version_info < (2, 6, 0):
    import simplejson as json
else:
    import json

try:
    from collections \
        import \
            defaultdict
except ImportError:
    from bento.compat._collections \
        import \
            defaultdict

if sys.version_info < (2, 6, 0):
    from bento.compat._tempfile \
        import \
            NamedTemporaryFile
else:
    from tempfile \
        import \
            NamedTemporaryFile

if sys.version_info < (2, 5, 0):
    from bento.compat.__tarfile_c \
        import \
            TarFile
else:
    from tarfile \
        import \
            TarFile

try:
    from functools import partial
except ImportError:
    from bento.compat._functools import partial

from bento.compat.misc \
    import \
        MovedModule, _MovedItems

_moved_attributes = []

if sys.version_info < (2, 7, 0):
    _moved_attributes.append(MovedModule("unittest", "unittest2"))
else:
    _moved_attributes.append(MovedModule("unittest", "unittest"))

for attr in _moved_attributes:
    setattr(_MovedItems, attr.name, attr)
del attr

moves = sys.modules["bento.compat.api.moves"] = _MovedItems("moves")
