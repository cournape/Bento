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
