"""toydist version of setup.py."""
from distutils.core import setup

from bento.import PackageDescription

info_dict = PackageDescription.form_file('bento.info').to_dict()
setup(**info_dict)
