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
           DATADIR as DATA_DIR
except ImportError:
    # Arch-independent path
    DATA_DIR = os.path.dirname(__file__)

# Arch-dependent path
ARCH_DATA_DIR = DATA_DIR

# Windows binaries
_CLI = os.path.join(ARCH_DATA_DIR, "commands", "cli.exe")
WININST_DIR = os.path.join(ARCH_DATA_DIR, "commands", "wininst")

# Parser parameters
_PICKLED_PARSETAB = os.path.join(DATA_DIR, "parsetab")
_OPTIMIZE_LEX = 0
_DEBUG_YACC = 0

_BUILD_DIR = "build"
# Use subdist bento to avoid clashing with distutils ATM
_SUB_BUILD_DIR = "bento"
BUILD_DIR = os.path.join(_BUILD_DIR, _SUB_BUILD_DIR)

# FIXME: we are progressively converting everything to node, meaning paths here
# will be relatively to the build directory. Path defined from BUILD_DIR are
# the ones which use API not node-compliant yet, the ones defined from
# _SUB_BUILD_DIR already are
CONFIGURED_STATE_DUMP = os.path.join(_SUB_BUILD_DIR, ".config.bin")
PKG_CACHE = os.path.join(BUILD_DIR, ".pkg.cache")
DB_FILE = os.path.join(BUILD_DIR, "cache.db")
CHECKSUM_DB_FILE = os.path.join(BUILD_DIR, "checksums.db")
ARGS_CHECKSUM_DB_FILE = os.path.join(BUILD_DIR, "argchecksums.db")
DISTCHECK_DIR = os.path.join(BUILD_DIR, "distcheck")
IPKG_PATH = os.path.join(BUILD_DIR, "ipkg.info")

BENTO_SCRIPT = "bento.info"

USE_PRIVATE_MODULES = True
