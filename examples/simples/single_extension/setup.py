from distutils.core import setup
from toydist.core import PackageDescription
from toydist.conv import pkg_to_distutils

pkg = PackageDescription.from_file("toysetup.info")
setup(**pkg_to_distutils(pkg))
