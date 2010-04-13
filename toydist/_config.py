"""
This module centralizes every internal configuration parameter used throughout
toydist.
"""
import os

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

CONFIGURED_STATE_DUMP = ".config.bin"
