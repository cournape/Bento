from toydist.core.package import \
        PackageDescription, static_representation
from toydist.conv import \
        distutils_to_package_description

try:
    from toydist.__dev_version import version as __version__
    from toydist.__dev_version import git_revision as __git_revision__
except ImportError:
    from toydist.__version import version as __version__
    from toydist.__version import git_revision as __git_revision__
