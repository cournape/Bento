import os

DATA_PATH = os.path.dirname(__file__)
ARCH_DATA = os.path.dirname(__file__)

_PICKLED_PARSETAB = os.path.join(DATA_PATH, "parsetab")
_OPTIMIZE_LEX = 0
_DEBUG_YACC = 0

_CLI = os.path.join(ARCH_DATA, "commands", "cli.exe")
