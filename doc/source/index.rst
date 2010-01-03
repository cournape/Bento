.. Toydist documentation master file, created by
   sphinx-quickstart on Sun Jan  3 12:53:13 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Toydist: an experimental alternative to distutils and setuptools
================================================================

Toydist is a Python-based packaging solution intended to replace
distutils/setuptools. Toydist is born out of my frustration dealing with
distutils/setuptools idiosyncraties and limitations when working with complex
builds such as numpy, scipy or matplotlib. It is designed with the following
philosophy in mind:

    - More pythonic: simple, hackable, explicit and one way to do it.
    - Extensibility: avoid tight internal coupling, make it possible to plug-in
      real build tools like scons or waf, and enable customization of the
      compilation process.
    - Take inspiration from existing tools in other communities: autotools,
      cabal, etc...
    - Internally decouple build, package description and packaging.
    - No dependency on any distutils or setuptools code.
    - Maintain backward-compatibility through conversion tools instead of
      maintaining compatibility with the deeply flawed distutils "API".
    - Simpler, and more obvious behavior compared to distutils/setuptools for
      simple projects

It is currenly in very early stage, and is not recommended for any production
use. Discussions on toydist design happens on the NumPy Mailing List.

Simple example
--------------

From existing setup.py
~~~~~~~~~~~~~~~~~~~~~~

Toymaker, the toydist command line interface has an experimental convert
command to convert existing setup.py::

    toymaker convert

If successfull, it will write a file named toysetup.info.

From scratch
~~~~~~~~~~~~

A simple python distribution named hello, with one package hello::

    hello/__init__.py
    hello/...

may be described as follows::

    Name: hello
    Version: 1.0

    Library:
        Packages:
            hello

Building and installing
~~~~~~~~~~~~~~~~~~~~~~~

Toydist includes toymaker, a command-line interface to toydist to configure,
build and install simple packages::

    toydist configure --prefix=somedirectory
    toydist build
    toydist install
    toydist sdist
    toydist build_egg

Features
--------

* Package descriptions are done in a declarative file (inspired from Cabal and
  RPM .spec files), so you can easily introspect basic features of packages.
* Include toymaker, a command line interface to configure, build, install
  projects.
* Easy integration with native filesystem conventions: every install directory
  is customizable at the configure stage (autoconf-inspired).
* Building eggs does not require depending on setuptools anymore.

Future features
---------------

* Simple C-extension building framework to cut distutils dependency
* Scons/waf libraries to interact with scons and waf build tools

Inspirations
------------

The main initial inspiration for toydist was Cabal, the packaging tool used in
the Haskell community.

I have also "stole" features from other similar solutions:

    * Autotools: flexible install scheme (autoconf), extra files installation (automake)
    * SCons/Waf: tool design, mini build framework
    * Setuptools: exe-based script generation on windows, egg format

.. Contents:

.. toctree::
   :maxdepth: 2

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

