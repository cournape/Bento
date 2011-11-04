"""
Bento, a pythonic packaging solution for python software.

Bento is a packaging solution which aims at being simple and extensible, using
as little magic as possible. Packages are described in a bento.info file which
has a straightforward syntax, and the packaging is driven through bentomaker,
the command line interfance to bento. Sane API are provided so that people can
build their own deployment facilities on top of it.

The code is currently organized as follows:
    - bento.core.parser: ply-based lexer/parser for the format
    - bento.core: core facilities to build package representation
    - bento.commands: commands as provided by bentomaker
    - bento.private: bundled packages
    - bento.compat: compatibility code to provide consistent API to all
      supported python versions (2.4 -> 2.7 ATM)
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

from bento.core.package import \
        PackageDescription, static_representation
from bento.conv import \
        distutils_to_package_description

try:
    from bento.__dev_version import version as __version__
    from bento.__dev_version import git_revision as __git_revision__
except ImportError:
    from bento.__version import version as __version__
    from bento.__version import git_revision as __git_revision__
