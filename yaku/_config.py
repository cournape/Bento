"""Global configuration

__file__, etc... are only allowed in this module.
"""
from os.path \
    import \
        join, abspath, dirname

TOOLDIRS = [abspath(join(dirname(__file__), "tools"))]

BUILD_DIR = "build"

# Use dot in the name to avoid accidental import of it
DEFAULT_ENV = join(BUILD_DIR, "default.env.py")
BUILD_CONFIG = join(BUILD_DIR, "build.config.py")
HOOK_DUMP = join(BUILD_DIR, ".hooks.pck")

CONFIG_CACHE = join(BUILD_DIR, ".config.pck")
BUILD_CACHE = join(BUILD_DIR, ".build.pck")
