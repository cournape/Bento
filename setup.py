import setuptools
from distutils.core import setup

DESCR = """\
Toydist is a toy distribution tool for python packages, The goal are
extensibility, flexibility, and easy interoperation with external tools.

As its name indicate, that's a toy packaging tool, which is only used as a
'straw' man for experimentation
"""

CLASSIFIERS = [
    "Development Status :: 1 - Planning",
    "Intended Audience :: Developers",
    "License :: OSI Approved",
    "Programming Language :: Python",
    "Topic :: Software Development",
    "Operating System :: Microsoft :: Windows",
    "Operating System :: POSIX",
    "Operating System :: Unix",
    "Operating System :: MacOS"
]

METADATA = {
    'name': 'toydist',
    'version': '0.0.1',
    'description': 'A toy distribution tool',
    'url': 'http://github.com/cournape/toydist',
    'author': 'David Cournapeau',
    'author_email': 'cournape@gmail.com',
    'license': 'BSD',
    'long_description': DESCR,
    'platforms': 'any',
    'classifiers': CLASSIFIERS,
}

PACKAGE_DATA = {
    'packages': ['toydist', 'toydist.compat', 'toydist.config_parser']
}

if __name__ == '__main__':
    config = {}
    for d in (METADATA, PACKAGE_DATA):
        for k, v in d.items():
            config[k] = v
    setup(**config)
