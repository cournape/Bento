"""toydist version of setup.py."""
from distutils.core import setup

from toydist import parse_static

info_dict = parse_static('toysetup.info').to_dict()
print info_dict
setup(**info_dict)
