Usage
-----

The core idea is to use a static file instead of python code in setup.py to
describe a package. Not only the metadata, but also the package content, C
source files, etc\.\.\. The goal is to be able to build, install and produce
installers/distributions from the static data, so that the setup.py looks like::

        from distutils.core import setup
        from bento import parse_static

        static_info = parse_static('setup.static').to_dict()
        setup(\*\*static_info)

There is also a function to do the contrary, that is generating the static file
from a standard setup.py::

        from distutils.core import setup, Extension
        from bento import distutils_to_package_description, \
                static_representation

        from distutils.core import setup, Extension

        dist = setup(name='hello',
                     version='1.0',
                     packages=['hello'],
                     ext_modules=[Extension('hello._bar', ['src/hellomodule.c'])])

        # The code below can be used to generate a setup.info, which can then be used
        # to feed a totally new build tool
        pkg = distutils_to_package_description(dist)
        open('setup.static', 'w').write(static_representation(pkg))
