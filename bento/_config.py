"""
This module centralizes every internal configuration parameter used throughout
bento.
"""
import os
import sys

import bento

# Arch-independent path
DATA_PATH = os.path.dirname(__file__)
# Arch-dependent path
ARCH_DATA = os.path.dirname(__file__)
WININST_DIR = os.path.join(os.path.dirname(__file__), "commands", "wininst")

# Parser parameters
_PICKLED_PARSETAB = os.path.join(DATA_PATH, "parsetab")
_OPTIMIZE_LEX = 0
_DEBUG_YACC = 0

# Windows binaries
_CLI = os.path.join(ARCH_DATA, "commands", "cli.exe")

# Use subdist bento to avoid clashing with distutils ATM
BUILD_DIR = "build/bento"
CONFIGURED_STATE_DUMP = os.path.join(BUILD_DIR, ".config.bin")
PKG_CACHE = os.path.join(BUILD_DIR, ".pkg.cache")
DISTCHECK_DIR = os.path.join(BUILD_DIR, "distcheck")

TOYDIST_SCRIPT = "bento.info"

USE_PRIVATE_MODULES = True
if USE_PRIVATE_MODULES:
    sys.path.insert(0, os.path.join(os.path.dirname(bento.__file__), "private", "_yaku"))
