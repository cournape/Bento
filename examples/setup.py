import os
from distutils.core import setup

from toydist.package import PackageDescription

CONFIG = {
    'name': 'foo',
    'version': '1.0',
    'url': 'http://example.com',
    'author': 'John Doe',
    'author_email': 'john@doe.com',
    'py_modules': ['foo']
}

if __name__ == '__main__':
    if os.path.exists('MANIFEST'):
        os.remove('MANIFEST')
    pkg = PackageDescription(**CONFIG)
    setup(**pkg.to_dict())
