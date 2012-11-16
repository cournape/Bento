"""
This module centralizes every internal configuration parameter used throughout
bento.
"""
import os
import sys

import bento

try:
    from bento.__config_py \
        import \
           PKGDATADIR, SITEDIR
except ImportError:
    # Arch-independent path
    PKGDATADIR = os.path.abspath(os.path.dirname(__file__))
    SITEDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# Windows binaries
_CLI = os.path.join(PKGDATADIR, "commands", "cli.exe")
WININST_DIR = os.path.join(PKGDATADIR, "commands", "wininst")

# Parser parameters
_PICKLED_PARSETAB = os.path.join(PKGDATADIR, "parsetab")
_OPTIMIZE_LEX = 0
_DEBUG_YACC = 0

# Use subdist bento to avoid clashing with distutils ATM
_SUB_BUILD_DIR = "bento"

CONFIGURED_STATE_DUMP = os.path.join(_SUB_BUILD_DIR, ".config.bin")
DB_FILE = os.path.join(_SUB_BUILD_DIR, "cache.db")
DISTCHECK_DIR = os.path.join(_SUB_BUILD_DIR, "distcheck")
BUILD_MANIFEST_PATH = os.path.join(_SUB_BUILD_DIR, "build_manifest.info")

BENTO_SCRIPT = "bento.info"

USE_PRIVATE_MODULES = True
