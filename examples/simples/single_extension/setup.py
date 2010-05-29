from distutils.core import setup
from bento.core import PackageDescription
from bento.conv import pkg_to_distutils

pkg = PackageDescription.from_file("bento.info")
setup(**pkg_to_distutils(pkg))
