========
Tutorial
========

This tutorial will guide you through the basics to package your python
code with bento. Note that for an existing project using
setup.py-based packaging, you should look at the convert command so
that you don't have to start from scratch.

Packaging a python module
=========================

First, let's assume you have a simple software fubar consisting of a
single python module hello.py::

    hello.py

A simple bento.info file would look as follows::

    Name: fubar
    Author: John Doe
    Summary: a simple module

    Library:
        Modules: hello.py

The indentation must be done through spaces (tabs are considered
syntax errors). The bento.info is located just next to your hello.py::

    hello.py
    bento.info

That's it, you have your first bento package !

Bentomaker
----------

Currently, the only way to interact with bento is bentomaker, a
command-line interface to bento. It is used to build, install and test
packages from the command line::

    bentomaker configure
    bentomaker build
    bentomaker install

You can also build eggs, source tarballs and windows installers
(windows only for now):: 

    bentomaker sdist
    bentomaker build_egg
    bentomaker build_wininst

You can access the list of available commands with the help command::

    bentomaker help commands

.. If you don't want to force your users to install bento to install your
.. software, you can include a single-file distribution of bento in your
.. own package, at the cost of adding a few hundred kiloytes to your
.. package.

Adding packages
===============

Adding a package (a directory with a __init__.py file) is simple as
well.  Assuming the following source tree::

    fubar/hello.py
    fubar/foo/__init__.py
    fubar/foo/bar.py

You simply write::

    Library:
        Packages: foo

Packages should be a comma separated list, and respect indentation::

    Library:
         Packages: foo, bar

works, as well as::

    Library:
        Packages:
            foo, bar

Adding data files
=================

Besides packages and modules, you may want to add extra files, like
configuration, manpages, documentation, etc... Those are called data
files.  Bento has a simple but powerful way to install arbitrary data
in arbitrary locations.

Installed vs non-installed files
--------------------------------

Bento has two distinct categories of data files:

    * installed files (data files): those files are part of the
      installed package
    * extra source files: those files are not installed, but part of
      the source distribution. They may be README, or additional files
      necessary to build the software.

An extra source file will only be included in the source tarballs,
whereas data files are installed and needed to use the software.

Installed data files: DataFiles section
---------------------------------------

Say our fubar software has one manpage fubar.1::

    fubar/fubar.1

We need to add the following to bento.info::

    DataFiles: manpage
        TargetDir: /usr/man/man1
        Files: fubar/fubar.1

This will install the file fubar/fubar.1 into /usr/man/man1 (as
/usr/man/man1/fubar/fubar.1)

Extra source files
------------------

Extra source files are added through the ExtraSourceFiles section::

    ExtraSourceFiles:
        setup.py
        test/*.py

Adding extensions
=================

Extension (compiled python modules) are supported as well. If you have
an extension _hello built from the file hellomodule.c, you just
write::

    Library:
        Extension: _hello
            Sources: hellomodule.c

Adding compiled libraries
=========================

Similarly, if you have a compiled library (a C library which is not
importable from python)::

    Library:
        CompiledLibrary: foo
            Sources: foo.c

Note that there is only one Library section, i.e. a package with both
extensions and compiled libraries would look like::

    Library:
        Extension: _hello
            Sources: hellomodule.c
        CompiledLibrary: foo
            Sources: foo.c

and not like::

    Library:
        Extension: _hello
            Sources: hellomodule.c
    Library:
        CompiledLibrary: foo
            Sources: foo.c

Adding executables
==================

Many python softwares are libraries, and their only use is from a
python interpreter. Nevertheless, it is relatively common to provide a
full program, be it GUI or command line tool. Bento uses a feature
similar to setuptools to help you create "entry points" which work on
both unix and windows systems::

    Executable: foomaker
        Module: foomakerlib.foomaker
        Function: main

This tells bento to create a script called foomaker (foomaker.exe on
windows), which calls the main function from the foomakerlib.foomaker
python module. Those scripts are automatically installed in $bindir
(which translates to /usr/local/bin by default on unix, and
C:\Python*/Scripts on windows, both values which may be changed by the
user at the configure stage).
