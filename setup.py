# setuptools should be first so that bento.distutils knows what to monkey patch
import setuptools
import bento.distutils
bento.distutils.monkey_patch()

from setup_common \
    import \
        generate_version_py

if __name__ == '__main__':
    generate_version_py("bento/__dev_version.py")
    setuptools.setup()
