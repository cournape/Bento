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

Bentomaker
----------

Currently, bentomaker is the main interface to the bento.info file,
and is used to build, install and test packages from the command
line::

    bentomaker configure
    bentomaker build
    bentomaker install

You can also build eggs, source tarballs and windows installers
(windows only for now):: 

    bentomaker sdist
    bentomaker build_egg
    bentomaker build_wininst

If you don't want to force your users to install bento to install your
software, you can include a single-file distribution of bento in your
own package, at the cost of adding a few hundred kiloytes to your
package.

Adding packages
===============

Adding a package (a directory with a __init__.py file) is as simple.
Assuming the following source tree::

    fubar/hello.py
    fubar/foo/__init__.py
    fubar/foo/bar.py

You simply write::

    Library:
        Packages: foo

Adding data files
=================

TODO

Adding extensions
=================

TODO
