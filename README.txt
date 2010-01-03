A toy distribution system for python strongly inspired by the Haskell _Cabal
system.

.. _Cabal: http://www.haskell.org/cabal/release/cabal-latest/doc/users-guide/

Simple examples
===============

From existing setup.py
----------------------

toymaker, the toydist command line interface has an experimental convert
command to convert existing setup.py::

    toymaker convert

If successfull, it will write a file toysetup.info

From scratch
------------

A simple python distribution named hello, with one package hello::

    hello/__init__.py
    hello/...

may be described as follows::

    Name: hello
    Version: 1.0

    Library:
        Packages:
            hello

Note that for now, you *have* to use 4 spaces for indentation, always. This is
an arbitrary limitation which will be removed at some point once the parser is
improved.

Building, installing
--------------------

Assuming the file is named toysetup.info, the command line interface toymaker
can be used to configure, build, install, etc... the distribution::

    toymaker configure --prefix=/usr/local
    toymaker build
    toymaker install
    toymaker sdist

Main design decisions
=====================

There isn't anything to see, as it is mostly used as a prototype to experiment
with different ideas I have to improve the distribution mess in python
community. The core principles are drawn from my own experience using and
extending complex build systems, as well as maintaining numpy.distutils
extensions.

The core design decisions are:

    * simple, explicit and one obvious way to do it
    * package description in a custom, limited language, to avoid running
      untrusted code
    * easy and stable interface with 3rd party build tools like make or
      scons when the custom package description is not enough
    * interoperate with existing python packaging infrastructure through
      file format, tools and protocol, not API
    * follow autoconf conventions for install directories, with
      platform-specific defaults.

What can it do
==============

Not much ATM. The following is implemented:

    * Basic library to parse the static format. The format support the
      following:

        * Most (all?) metadata from PKG-INFO format 1.2
        * Command line options for additional path and flags
        * One simple way to deal with installed data files
        * One simple wat to deal with non-installed data (e.g. only
          included in sdist)
        * Packages, modules and simple C extensions

    * Building and installing simple packages from the static
      format (Linux and Mac OS X only for now), sdist generation
    * Experimental automatic convertion of existing setup.py to a new
      static format
    * Basic egg generation

Static metadata
===============

At this point, the format is still in flux, the supported features are
described below.

Simple metadata
---------------

A simple static file looks like this::

    Name: hello
    Author: John Doe
    Version: 1.0

    Library:
        Packages:
            hello

Data files
~~~~~~~~~~

Toydist makes the difference between installed data and extra source files,
which are only to be included in source tarballs and the like (i.e. only
necessary at build times).

Installed data files are declared as follows::

    Name: hello
    Author: John Doe
    Version: 1.0

    Datafiles:
        target=/etc
        files:
            config.cfg

This means that the file config.cfg will be installed in /etc. The full name of
the files entries are used when installing, e.g.::

    Datafiles:
        target=/etc
        files:
            config/config.cfg

Will install config/config.cfg as /etc/config/config.cfg. To install it as
/etc/config.cfg, you should use the srcdir argument::

    Datafiles:
        srcdir=config
        target=/etc
        files:
            config.cfg

Any data file which is not installed is declared as follows::

    ExtraSourceFiles:
        foo.cfg,
        toysetup.info,

Those will never be installed.

Path options
~~~~~~~~~~~~

Additional path options may be added. For example, toydist does not handle
documentation yet, so to install e.g. a manpage, you could do as follows::

    Path: mandir1
        Description: man 1 directory
        Default: $datadir/man/man1

The path can then be used as follows::

    DataFiles:
        srcdir=doc/man
        target=$mandir1
        files:
            foo.1

And will install the file doc/man/foo.1 into $mandir. The toymaker utility can
be used to customize the path, e.g.::

    toymaker configure -h # list the option --mandir1 with its description
    toymaker configure --mandir1=/usr/local/share/man/man1

Rationale
=========

Being able to describe most python packages from a purely static file has the
following advantages:

    * No arbitrary code execution, you only have to trust toydist code
      instead of setup.py (which can do anything that python can)
    * Inspection of packages becomes easier for third parties, like OS
      vendors.
    * Also the current toydist implementation uses distutils to actually
      build the extensions, distutils becomes an implementation detail of
      the system, in the sense that another build system can be build on
      top of toydist. This gives a simple but powerful way forward for
      improving the situation of python packaging.

Useful discussions which are related to toydist design:

    * BUILDS (never passed the design stage AFAIK): http://mail.python.org/pipermail/distutils-sig/2008-October/010343.html
    * Going away from setup.py: http://www.mail-archive.com/distutils-sig@python.org/msg08031.html
    * `Just use debian' on distutils-sig: http://mail.python.org/pipermail/distutils-sig/2008-September/010129.html
