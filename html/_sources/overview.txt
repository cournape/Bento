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
    bentomaker install

If you are fine with default configuration values, you can install in one step::

    bentomaker install

You can check where bento install files with the --list-files option (in which
case bento does not install anything)::

    bentomaker install --list-files

Bentomaker contains a basic help facility, which list existing commands,
etc...::

    bentomaker help commands # list commands

From existing setup.py
~~~~~~~~~~~~~~~~~~~~~~

Bentomaker has an experimental convert command to convert an existing setup.py::

    bentomaker convert

If successfull, it will write a file named bento.info. The convert command is
inherently fragile, because it has to hook into distutils/setuptools internals.
The more setup.py relies on distutils extensions, the less likely the convert
command will be successful

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

Adding bento-based setup.py for compatibility with pip, etc...
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Although nothing fundamentally prevents bento to work under installers such as
pip, pip currently does not know anything about bento. To help transition,
bento has a distutils compatibility layer. A setup.py as simple as::

    import setuptools
    import bento.distutils

    from setuptools import setup

    if __name__ == '__main__':
        setup()

will enable commands such as::

    python setup.py install
    python setup.py sdist

to work as expected, taking all the package information from bento.info file.

Note:: obviously, this mode will not enable all the features offered by bento.
If it were possible, bento would not have been written in the first place.
Nevertheless, the following commands should work relatively well as long as you
don't have hooks:

    * sdist
    * bdist_egg
    * install

This should be enough for pip install foo or easy_install foo to work for a
bento-based package.
