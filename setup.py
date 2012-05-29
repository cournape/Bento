# setuptools should be first so that bento.distutils knows what to monkey patch
import setuptools
import bento.distutils
bento.distutils.monkey_patch()

if __name__ == '__main__':
    setuptools.setup()
