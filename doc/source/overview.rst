Overview
========

Bento is based on a declarative package description, which is parsed by the
different build tools to do the actual work. There are currently two ways to
create such a package description: by writing it from scratch, or by converting
an existing setup.py.

Simple example
--------------

From scratch
~~~~~~~~~~~~

Bento packages are created from a bento.info file, which describes
metadata as well as package content in a mostly declarative manner.

For a simple python package hello consisting of two files::

    hello/__init__.py
    hello/hello.py

a simple bento.info may be written as follows::

    Name: hello
    Version: 1.0

    Library:
        Packages:
            hello

The file contains some metadata, like package name and version. Its syntax is
indentation-based, like python, except that only spaces are allowed (tab
character will cause an error when used at the beginning of a line).

Building and installing
~~~~~~~~~~~~~~~~~~~~~~~

Bento includes bentomaker, a command-line interface to configure, build and
install simple packages. Its interface is similar to autotools::

    bentomaker configure --prefix=somedirectory
    bentomaker build
    bentomaker install

In addition, the following subcommands are available::

    bentomaker sdist

to build a source distribution and::

    bentomaker build_egg

to build an egg. Building an egg requires to run configure and build first -
this is not done automatically (yet).

From existing setup.py
~~~~~~~~~~~~~~~~~~~~~~

Bentomaker has an experimental convert command to convert an existing setup.py::

    bentomaker convert

If successfull, it will write a file named bento.info. The convert command
is inherently fragile, because it has to hook into distutils/setuptools
internals.

Note: because the convert command does not parse the setup.py, but runs it
instead, it only handles package description as defined by one run of setup.py.
For example, bento convert cannot automatically handle the following
setup.py::

    import sys
    from setuptools import setup

    if sys.platform == "win32":
        requires = ["sphinx", "pywin32"]
    else:
        requires = ["sphinx"]

    setup(name="foo", install_requires=requires)

If run on windows, the generated bento.info will be::

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

Note:: bento syntax supports simple conditional, so after conversion, you
could modify the generated file as follows::

    Name: foo

    Library:
        InstallRequires:
            sphinx
        if os(win32):
            InstallRequires:
                pywin32
