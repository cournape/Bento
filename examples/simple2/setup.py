"""The simplest package you can imagine: one module (one file), name and
version metadata only.
"""
from distutils.core import setup

dist = setup(name='foo',
             version='1.0',
             packages=['foo'])

# The code below can be used to generate a setup.info, which can then be used
# to feed a totally new build tool
from toydist import \
        distutils_to_package_description, static_representation

pkg = distutils_to_package_description(dist)
print static_representation(pkg)
