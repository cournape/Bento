Overview
========

Bento aims at simplifying the packaging of python softwares, both from the user
and developer point of view. Bento packages are described by a bento.info file,
which is parsed by the different build tools to do the actual work. Currently,
the main user interface to bento is bentomaker, a command line tool to build,
install and query bento packages.

There are currently two ways to create bento packages : by writing a bento.info
file from scratch, or by converting an existing setup.py.

Simple example
--------------

Those examples assume you have already a usable bentomaker in your PATH, either
through bento installation or by using the one-file bentomaker bundle. If you
can execute::

    bentomaker help

successfully, you should be able to go on.

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

You use bentomaker to build and install bento packages.  Its interface is
similar to autotools::

    bentomaker configure --prefix=somedirectory
    bentomaker install

If you are fine with default configuration values, you can install in one step::

    bentomaker install

bentomaker will automatically determine which commands need to be re-run.  You
can check where bento install files with the --list-files option (in which case
bento does not install anything)::

    bentomaker install --list-files

Bentomaker contains a basic help facility, which list existing commands,
etc...::

    bentomaker help commands # list commands

From existing setup.py (convertion from distutils-based projects)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Bentomaker has an experimental convert command to convert an existing setup.py::

    bentomaker convert

If successfull, it will write a bento.info file whose content is derived from
your setup.py. The convert command is inherently fragile, because it has to
hook into distutils/setuptools internals. Nevertheless, it has been used
succesfully to convert packages such as Sphinx or Jinja.
