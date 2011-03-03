---------------------------
bento.info format reference
---------------------------

Introduction
============

The package description is a text file, by default named bento.info. Its syntax
is indentation-based. It does not support yet commenting, and is currently
limited to ASCII.

A typical .info file is structured as follows:

    * The package metadata (name, version, etc...)
    * Optionally, it may contain addition user-customizable options such as
      path or flags, whose exact value may be set at configure time.
    * A Library section, which defines the package content (packages, modules,
      C extensions, etc...)
    * Optionally, the .info file may contain one or several Executable
      sections, to describe programs expected to be run from the command line
      or from a GUI. This is where distutils scripts and setuptools console
      scripts are defined.

Each section consists of field:value pairs:

    * Both fields and values are case-sensitive.
    * Indentation has to be in spaces, tab characters for indentation are not
      supported. Besides this constraints, rules for indentation should follow
      python's own rule (arbitrary number of spaces for a given indentation
      level).

Package metadata
================

Bento supports most metadata defined in the PEP 241 and 314.  For a simple
package containing one module hello, the bento.info metadata definition would
look like::

    Name: hello
    Version: 0.0.1
    Summary: A one-line description of the distribution
    Description:
        A longer, potentially multi-line string.

        As long as the indentation is maintained, the field is considered as
        continued.
    Author: John Doe
    AuthorEmail: john@doe.org
    License: BSD

Different fields have different values: they generally consist of either a word
(string sequence without a space), a line (a sequence of words without a
newline) or multiple lines (Description field only).

Note:: while most metadata defined in the PEP-241 and PEP-314 are supported
syntax-wise, their semantics are not always implemented already.

Note:: the bento lexer is ad-hoc and not well specified at this stage. It was
conceived to handle values in the reStructuredText format, but doing so
prevents desired flexibility of the bento.info format itself, or would be too
complex to support. Before 1.0, bento.info format may change so that fields in
reStructuredText need to be put in a separate file, e.g.::

    DescriptionFromFile: README.rst

If you are reading this and actually know something about parsing and have a
better idea to support inline reST, I am open to suggestions !

Name
----

Format::

    Name: ASCII_TOKEN

Name of the software being packaged. Its value should contain only
alpha-numeric characters.

Version
-------

Format::

    Version: VERSION_TOKEN

VERSION_TOKEN format is not enforced yet

Summary
-------

Format::

    Description: WORDS

One or more space separated words

Url
---

Author
------

Author email
------------

Maintainer
----------

Maintainer email
----------------

License
-------

Description
-----------

Platforms
---------

Classifiers
-----------

User-customizable flags
=======================

Library section
===============

Executable section
==================

Pure python packages
--------------------

Assuming a package with the following layout::

    hello/pkg1/__init__.py
    hello/pkg1/...
    hello/pkg2/__init__.py
    hello/pkg2/...
    hello/__init__.py

it would be declared as follows::

    Name: hello
    Version: 0.0.1

    Library:
        Packages:
            hello.pkg1,
            hello.pkg2,
            hello

The following syntax is also allowed::

    Library:
        Packages:
            hello.pkg1, hello.pkg2, hello

as well as::

    Library:
        Packages: hello.pkg1, hello.pkg2, hello

Packages containing C extensions
================================

For a simple extension hello._foo, built from sources src/foo.c and src/bar.c,
the declaration is as follows::

    Library:
        Extension: hello._foo
            Sources:
                src/foo.c,
                src/bar.c

Note: none of the other distutils Extension arguments (macro definitions,
etc...) are supported yet.

Packages with data files
========================

Adding data files in bento is easy. By data files, we mean any file other
than C extension sources and python files. There are two kinds of data files in bento:

    * Installed data files: those are installed somewhere on the user system at
      installation time (distutils package_data and data_files, numpy.distutils
      add_data_files and add_data_dir).
    * Extra source files: those are only necessary to build the package, and
      are not installed. As such, they only need to be included in the source
      tarball (distutils MANIFEST[.in] mechanism, automatic inclusion from the
      VCS in setuptools, etc...)

Extra source files
------------------

Extra source files are simply declared in the section ExtraSourceFiles (outside
any Library section)::

    ExtraSourceFiles:
        AUTHORS,
        CHANGES,
        EXAMPLES,
        LICENSE,
        Makefile,
        README,
        TODO,
        babel.cfg

Those will be always be included in the tarball generated by bento sdist. A
limited form of globbing is allowed::

    ExtraSourceFiles:
        doc/source/*.rst
        doc/source/chapter1/*.rst

that is globbing on every file with the same extension is allowed. Any other
form of globbing, in particular recursive ones are purposedly not supported to
avoid cluttering the tarball by accident.

Installed data files
--------------------

It is often needed to install data files within the rest of the package.
Bento's system is both simple and flexible enough so that any file in your
sources can be installed anywhere. The most simple syntax for data files is as
follows::

    DataFiles:
        TargetDir: /etc
        Files:
            somefile.conf

This installs the file somefile.conf into /etc. Using hardcoded paths should be
avoided, though. Bento allows you to use "dynamic" path instead. This scheme
should be familiar to people who have used autotools::

    DataFiles:
        TargetDir: $sysconfdir
        Files:
            somefile.conf

$sysconfigdir is a path variable: bento defines several path variables
(available on every platform), which may be customized at the configure stage.
For example, on Unix, $sysconfdir is defined as $prefix/etc, and prefix is
itself defined as /usr/local. If prefix is changed, sysconfdir will be changed
accordingly. Of course, sysconfdir itself may be customized as well. This
allows for very flexible installation layout, and every particular install
scheme (distutils --user, self-contained as in GoboLinux or Mac OS X) may be
implemented on top.

It is also possible to define your own path variables (see `Path option`_
section).

Srcdir field
~~~~~~~~~~~~

By default, the installed name is the concatenation of target and the values in
files, e.g.::

    DataFiles:
        TargetDir: $includedir
        Files:
            foo/bar.h

will be installed as $includedir/foo/bar.h. If instead, you want to install
foo/bar.h as $includedir/bar.h, you need to use the srcdir field::

    DataFiles:
        TargetDir: $includedir
        SourceDir: foo
        Files:
            bar.h

Named data files section
~~~~~~~~~~~~~~~~~~~~~~~~

You can define as many DataFiles sections as you want, as long as you name
them, i.e.::

    DataFiles: man1
        TargetDir: $mandir/man1
        SourceDir: doc/man
        Files:
            *.1

    DataFiles: man3
        TargetDir: $mandir/man3
        SourceDir: doc/man
        Files:
            *.3

is ok, but::

    DataFiles:
        TargetDir: $mandir/man1
        SourceDir: doc/man
        Files:
            *.1

    DataFiles:
        TargetDir: $mandir/man3
        SourceDir: doc/man
        Files:
            *.3

is not.

Available path variables
------------------------

By default, bento defines the following path variables:

    * prefix: install architecture-independent files
    * eprefix: install architecture-dependent files
    * bindir: user executables
    * sbindir: system admin executables
    * libexecdir: program executables
    * sysconfdir: read-only single-machine data
    * sharedstatedir: modifiable architecture-independent data
    * localstatedir: modifiable single-machine data
    * libdir: object code libraries
    * includedir: C header files
    * oldincludedir: C header files for non-gcc
    * datarootdir: read-only arch.-independent data root
    * datadir: read-only architecture-independent data
    * infodir: info documentation
    * localedir: locale-dependent data
    * mandir: man documentation
    * docdir: documentation root
    * htmldir: html documentation
    * dvidir: dvi documentation
    * pdfdir: pdf documentation
    * psdir: ps documentation

While some of those path semantics don't make sense on some platforms such as
windows, they are defined everywhere with defaults, to ensure a consistent
interface across platforms. They are also defined to to get a 1-to-1
correpondance with the autoconf conventions, which are familiar to most
packagers on open source OS and system administrators.

Conditionals
============

It is not always possible to have one same package description for every
platform. It may also be desirable to enable/disable some parts of a package
depending on some option. For this reason, the .info file supports a limited
form of conditional. For example::

    Library:
        InstallRequires:
            docutils,
            sphinx
            if os(windows):
                pywin32

The following conditional forms are available:

    - os(value): condition on the OS
    - flag(value): user-defined flag, boolean

Adding custom options
=====================

Path option
-----------

A new path option may be added::

    Path: octavedir
        Description: octave directory
        Default: $datadir/octave

Bentomaker automatically adds an --octavedir option (with help taken from the
description), and $octavedir may be used inside the .info file.

Flag option
-----------

A new flag option may be added::

    Flag: debug
        Description: build debug
        Default: false

Bentomaker automatically adds an --octavedir option (with help taken from the
description), and $octavedir may be used inside the .info file.
