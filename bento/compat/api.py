import os
import sys

if os.name == "posix":
    from posix_path \
        import \
            relpath
    rename = os.rename
elif os.name == "nt":
    from nt_path \
        import \
            relpath
    from rename import rename
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
