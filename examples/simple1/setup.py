"""The simplest package you can imagine: one module (one file), name and
version metadata only.
"""
from distutils.core import setup

dist = setup(name='foo',
             version='1.0',
             py_modules=['foo'])
