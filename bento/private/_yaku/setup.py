import os
import sys
import shutil

import setuptools
from distutils.core \
    import \
        setup

if sys.version_info >= (3,):
    local_path = os.path.dirname(__file__)
    src_path = os.path.join(local_path, 'build', 'py3k')
    sys.path.insert(0, os.path.join(local_path, 'tools'))
    import py3tool
    print("Converting to Python3 via 2to3...")
    py3tool.sync_2to3('yaku', os.path.join(src_path, 'yaku'))

setup(name="yaku",
    description="A simple build system in python to build python extensions",
    long_description=open("README").read(),
    version="0.0.1",
    author="David Cournapeau",
    author_email="cournape@gmail.com",
    license="BSD",
    packages=["yaku.tools", "yaku", "yaku.compat"],
)
