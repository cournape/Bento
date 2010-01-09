Overview
========

.. Toydist is born out of my frustration dealing with distutils/setuptools
.. idiosyncraties and limitations, especially when working with complex builds
.. such as numpy, scipy or matplotlib. Distutils is too complex for simple needs,
.. and too inflexible for complex builds.

.. Philosophy
.. ----------
.. 
.. Toydist's main characteristics are:
.. 
..     - Pythonic: simple, hackable, explicit and one way to do it.
..     - Extensibility: avoid tight internal coupling, make it possible to plug-in
..       real build tools like scons or waf, and enable customization of the
..       compilation process.
..     - Take inspiration from existing tools in other communities: autotools,
..       cabal, etc...
..     - Internally decouple build, package description and packaging.
..     - No dependency on any distutils or setuptools code.
..     - Maintain backward-compatibility through conversion tools instead of
..       maintaining compatibility with the deeply flawed distutils "API".
..     - Simpler, and more obvious behavior compared to distutils/setuptools for
..       simple projects

Toydist is based on a declarative package description, which is parsed by the
different build tools to do the actual work. There are currently two ways to
create such a package description: by writing it from scratch, or by converting
existing setup.py.

Simple example
--------------

From scratch
~~~~~~~~~~~~

Toydist packages are created from a toysetup.info file, which describes
metadata as well as package content in a mostly declarative manner.

For a simple package hello as follows::

    toysetup.info
    hello/__init__.py
    hello/hello.py

a simple toysetup.info may be written as follows::

    Name: hello
    Version: 1.0

    Library:
        Packages:
            hello

The file contains some metadata, like package name and version. Its syntax is
indentation-based, like python.

Important note: indentation is currently hardcoded to 4 spaces, i.e. every
indentation level must be exactly 4 spaces. A different number of spaces, or a
tab character will cause the parser to choke. This limitation will be
alleviated before a 1.0 release.

Building and installing
~~~~~~~~~~~~~~~~~~~~~~~

Toydist includes toymaker, a command-line interface to toydist to configure,
build and install simple packages. Its interface is similar to autotools::

    toydist configure --prefix=somedirectory
    toydist build
    toydist install

In addition, the following subcommands are available::

    toydist sdist

To build a source distribution and::

    toydist build_egg

To build an egg. Building an egg requires to run configure and build first -
this is not done automatically (yet).

From existing setup.py
~~~~~~~~~~~~~~~~~~~~~~

Toymaker has an experimental convert command to convert existing setup.py::

    toymaker convert

If successfull, it will write a file named toysetup.info. The convert command
is inherently fragile, because it has to hook into distutils/setuptools
internals.

Note: because the convert command does not parse the setup.py, but runs it
instead, it only handles package description as defined by one run of setup.py.
For example, toydist convert cannot automatically handle the following
setup.py::

    import sys
    from setuptools import setup

    if sys.platform == "win32":
        requires = ["sphinx", "pywin32"]
    else:
        requires = ["sphinx"]

    setup(name="foo", install_requires=requires)

If run on windows, the generated toysetup.info will be::

    Name: foo

    Library:
        InstallRequires:
            pywin32,
            sphinx

and::

    Name: foo

    Library:
        InstallRequires:
            sphinx

otherwise.
