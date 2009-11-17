A toy distribution system for python.

There isn't anything to see, as it is mostly used as a prototype to experiment
with different ideas I have to improve the distribution mess in python
community. The core principles are drawn from my own experience using and
extending complex build systems, as well as maintaining numpy.distutils
extensions.

The core design decisions are::

        * simple, explicit and one obvious way to do it
        * package description in a custom, limited language, to avoid running
          untrusted code
        * easy and stable interface with 3rd party build tools like make or
          scons when the custom package description is not enough
        * interoperate with existing python packaging infrastructure through
          file format, tools and protocol, not API

What can it do
==============

Not much ATM. The following is implemented::

	* Converting existing setup.py to a new static format
	* Building and installing packages from the static format using
	  distutils

Static metadata
===============

Rationale
---------

Being able to describe most python packages from a purely static file has the
following advantages::

	* No arbitrary code execution, you only have to trust toydist code
	  instead of setup.py (which can do anything that python can)
	* Inspection of packages becomes easier for third parties, like OS
	  vendors.
	* Also the current toydist implementation uses distutils to actually
	  does the building and packaging from the static description,
	  distutils becomes an implementation detail of the system, in the
	  sense that another build system can be build on top of toydist. This
	  gives a simple but powerful way forward for improving the situation
	  of python packaging.

Usage
-----

The core idea is to use a static file instead of python code in setup.py to
describe a package. Not only the metadata, but also the package content, C
source files, etc\.\.\. The goal is to be able to build, install and produce
installers/distributions from the static data, so that the setup.py looks like::

        from distutils.core import setup
        from toydist import parse_static

        static_info = parse_static('setup.static').to_dict()
        setup(\*\*static_info)

There is also a function to do the contrary, that is generating the static file
from a standard setup.py::

        from distutils.core import setup, Extension
        from toydist import distutils_to_package_description, \
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

Format
------

A simple static file looks like this::

        Name: hello
        Version: 1.0
        Package:
            hello
        Extension: hello._bar
            sources:
                src/hellomodule.c

The format is strongly inspired by the _Cabal system from Haskell.

.. _Cabal: http://www.haskell.org/cabal/release/cabal-latest/doc/users-guide/

