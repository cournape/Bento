"""Global configuration

__file__, etc... are only allowed in this module.
"""
import sys

from os.path \
    import \
        join, abspath, dirname

TOOLDIRS = [abspath(join(dirname(__file__), "tools"))]

# relative to the build directory
DEFAULT_ENV = "default.env.py"
BUILD_CONFIG = "build.config.py"
HOOK_DUMP = ".hooks.pck"

CONFIG_CACHE = ".config.pck"
BUILD_CACHE = ".build.pck"

_OUTPUT = sys.stdout
