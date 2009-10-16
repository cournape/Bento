"""A trivial package with some C code."""
from distutils.core import setup, Extension

dist = setup(name='hello',
             version='1.0',
             packages=['hello'],
             ext_modules=[Extension('hello._bar', ['src/hellomodule.c'])])

# # The code below can be used to generate a setup.info, which can then be used
# # to feed a totally new build tool
# from toydist import \
#         distutils_to_package_description, static_representation
# 
# pkg = distutils_to_package_description(dist)
# print static_representation(pkg)
