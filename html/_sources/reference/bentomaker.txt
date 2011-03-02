-----------------------------------------------
Bentomaker, the command line interface to bento
-----------------------------------------------

Introduction
============

Bentomaker is a simple python package which uses bento API to configure, build
and install packages. A simple install with bentomaker looks like this::

    bentomaker configure --prefix=/home/david/local
    bentomaker build
    bentomaker install

Or more simply::

    bentomaker configure --prefix=/home/david/local
    bentomaker install

bentomaker commands know which other command they depend on, and are
automatically run if necessary.

Bentomaker has a basic help facility::

    bentomaker help

will list all available commands. Once the project is configured, every
installation path and user customization is set up, and cannot be changed
(except by reconfiguring the package, of course).

Available commands
==================

configure
---------

This command must be run before any build/install command. It is similar to
the well-known configure script from autoconf. Every customizable option is
available from the command help::

    bentomaker configure -h

If the configure command is not run explicitely, it will automatically be run
by any subsequent command.

build
-----

This simply builds the package. For pure-python packages, it does almost
nothing, except producing a `Build manifest`_. For packages with C extensions,
the C extensions are built.

install
-------

build_egg
---------

This command builds an egg from the package description. It currently requires
that configure and build commands have been run.

*This is experimental - although I intend to produce eggs which are as backward
compatible as possible with existing tools (in particular enstaller, and
hopefully virtualenv and buildout), eggs are implementation defined, and depend
a lot on distutils idiosyncraties.*

sdist
-----

This simply produces a source tarball. Currently, only .tar.gz is supported.

convert
-------

This converts a package built from distutils, setuptools or numpy.distutils::

    bentomaker convert

If successful, it will produce a bento.info file.

*This is experimental, and may not work. Also, it cannot convert every package
accurately, as it is based on inspecting setup.py's execution*. Nevertheless,
it can already convert simple, but non trivial packages such as sphinx pretty
accurately.
