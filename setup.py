# setuptools should be first so that bento.distutils knows what to monkey patch
import setuptools
import bento.distutils

from setuptools \
    import \
        setup

if __name__ == '__main__':
    setup()
