import os
import sys

_MINVER = ".".join([str(i) for i in sys.version_info[:2]])

BENTO_HOME = os.path.join(os.path.expanduser("~"), ".bento")
LOG_DIR = os.path.join(BENTO_HOME, _MINVER, "ilogs")
BENTO_INSTALL_PREFIX = os.path.join(BENTO_HOME, _MINVER)
BENTO_DB = os.path.join(BENTO_HOME, _MINVER, "db", "packages.db")

SCRIPT_NAME = "bentoshop"
