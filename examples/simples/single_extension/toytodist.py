"""toydist version of setup.py."""
from distutils.core import setup
from bento.import PackageDescription
from bento.conv import package_description_to_distutils

pkg = PackageDescription.from_file('bento.info')
info_dict = package_description_to_distutils(pkg)
print info_dict
setup(**info_dict)
