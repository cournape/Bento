"""Global configuration

__file__, etc... are only allowed in this module.
"""
from os.path \
    import \
        join, abspath, dirname

TOOLDIRS = [abspath(join(dirname(__file__), "tools"))]
