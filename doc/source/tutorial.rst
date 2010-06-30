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

Besides packages and modules, you may want to add extra files, like
configuration, manpages, documentation, etc... Those are called data files.
Bento has a simple but powerful way to install arbitrary data in arbitrary
locations.

Say our fubar software has one manpage fubar.1::

    fubar/fubar.1

We need to add the following to bento.info::

    DataFiles: manpage
        TargetDir: /usr/man/man1
        Files: fubar.1

This will install the file fubar.1 into /usr/man/man1.

Flexible install scheme
-----------------------

Hardcoding the target directory as above is not flexibe. The user may want to
install the package somewhere else. Bento defines a set of variable paths which
are customizable, with platform-specific defaults (TODO: list). For manpages,
the variable is mandir::

    DataFiles: manpage
        TargetDir: $mandir/man1
        Files: fubar.1

Now, the installation path is customizable, e.g.::

    bentomaker configure --mandir=/opt/man

will cause the target directory to translate to /opt/man/man1. Note that if
directories are included in the values in Field, those are used to determine
the install directory, e.g.::

    DataFiles: manpage
        TargetDir: $mandir
        Files: man1/fubar.1, man3/barfu.3

will install man1/fubar1 as $mandir/man1/fubar.1 and man3/barfu.3 as
$mandir/man3/barfu.3. To avoid this behavior, you need to use the SourceDir
option::

    DataFiles: manpage
        TargetDir: $mandir
        SourceDir: man1
        Files: fubar.1

will install man1/fubar.1 as $mandir/fubar.1. Last, you can define your own new
path variables (TODO: path variable section).

Adding extensions
=================

TODO
