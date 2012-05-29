"""
Bento, a pythonic packaging solution for python software.

Bento is a packaging solution which aims at being simple and extensible, using
as little magic as possible. Packages are described in a bento.info file which
has a straightforward syntax, and the packaging is driven through bentomaker,
the command line interfance to bento. Sane API are provided so that people can
build their own deployment facilities on top of it.

The code is currently organized as follows:
    - bento.core: core facilities to handle package representation
    - bento.commands: commands as provided by bentomaker
    - bento.compat: compatibility code to provide consistent API to all
    - bento.parser: ply-based lexer/parser for the bento.info format
    - bento.private: bundled packages
"""
import sys
import os

import os.path as op

from bento._config \
    import \
        USE_PRIVATE_MODULES

# FIXME: there has to be a better way to do this ?
for bundled_pkg in ["_ply", "_simplejson", "_yaku", "_six"]:
    v = "BENTO_UNBUNDLE%s" % bundled_pkg.upper()
    if USE_PRIVATE_MODULES and not os.environ.get(v, False):
        m_path = op.join(op.dirname(__file__), "private", bundled_pkg)
        # XXX: we always add bundled packages for now because checking for file
        # existence is too naive (does not work for zip-import)
        sys.path.insert(0, m_path)

try:
    import __package_info
except ImportError:
    __version__ = 'nobuilt'
    __git_revision__ = 'nobuilt'
else:
    from __package_info import VERSION as __version__, GIT_REVISION as __git_revision__
