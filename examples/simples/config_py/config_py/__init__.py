import os

try:
    from config_py.__config import PKGDATADIR
except ImportError:
    PKGDATADIR = os.path.join(os.path.dirname(__file__), os.pardir, "data")

print os.path.exists(os.path.join(PKGDATADIR, "foo.stat"))
