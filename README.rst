A pythonic, no-nonsense packaging tool for python software. Packaging is as
simple as writing a file toysetup.info with a file which looks as follows::

    Name: Foo
    Author: John Doe

    Library:
        Packages: foo

The package is then installed with toymaker, the command line interface to
toydist::

    toymaker configure
    toymaker build
    toymaker install

The goals of toydist are simplicity and extensibility. There should be only one
way to package simple packages (ideally, relying only on the toysetup.info
file), while being flexible enough to handle complex softwares. The ultimate
goal of toydist is to replace the hideous distutils extensions to build NumPy
and SciPy.

The main features of toydist are:

    * Indentation-based declarative package description
    * Automatic conversion from setup.py to toydist format
    * Support for arbitrary installation scheme (ala autoconf, with sensible
      defaults on Windows)
    * Simple and flexible data files installation description
    * Basic support for console scripts ala setuptools
    * Preliminary support for building eggs and windows installers

Planned features:

    * Support for msi and Mac OS X .mpkg
    * Enable Linux distributors to write simple extensions for packaging
      toydist-packages as they see fit
    * Pre/Post stages hooks
    * Distutils compatibility mode, driven by the toysetup.info file
    * Protocol to integrate with real build tools like scons, waf or
      make
    * Infrastructure for a correctly designed package index, using
      well-known practices instead of the broken easy_install + pypi
      model (easy mirroring, enforced metadata, indexing to enable
      querying-before-installing, etc...).

Code-wise, toydist has the following advantages:

    * Clear separation of intent between package description, configuration,
      build and installation
    * No dependency on distutils or setuptools code, with a focus on
      using standard python idioms

Toydist discussion happen on NumPy Mailing list, and development is on
`github`_. Bugs should be reported on toydist `issue-tracker`_. Online
`documentation`_ is available on github as well.

TOYDIST IS IN (VERY) EARLY STAGES: ANY PRODUCTION USAGE IS STRONGLY DISCOURAGED
AT THIS POINT.

.. _github: http://github.com/cournape/toydist.git
.. _issue-tracker: http://github.com/cournape/toydist/issues
.. _documentation: http://cournape.github.com/toydist

Installing toydist
------------------

Toydist may be installed the usual way from setup.py::

    python setup.py install --user # python 2.6 and later
    python setup.py install --prefix=some_directory

Alternatively, there is a bootstrap script so that toydist can install itself::

    python bootstrap.py # create the toymaker[.exe] script/executable 
    ./toymaker configure && ./toymaker build && ./toymaker install

Quick starting guide for packaging with toydist
-----------------------------------------------

From existing setup.py
~~~~~~~~~~~~~~~~~~~~~~

toymaker, the toydist command line interface has an experimental convert
command to convert existing setup.py::

    toymaker convert

If successfull, it will write a file toysetup.info. If it fails,
convert.log should contain useful information. If the conversion
fails, please report a bug on the `issue-tracker`_, but keep in mind
that complex packages cannot be fully converted, especially if they
rely on complex distutils extensions.

From scratch
~~~~~~~~~~~~

A simple python distribution named hello, with one package hello::

    hello/__init__.py
    hello/...

may be described as follows::

    Name: hello
    Version: 1.0

    Library:
        Packages:
            hello

Building, installing
~~~~~~~~~~~~~~~~~~~~

Assuming the file is named toysetup.info, the command line interface toymaker
can be used to configure, build, install, etc... the distribution::

    toymaker configure --prefix=/usr/local
    toymaker build
    toymaker install
    toymaker sdist
    toymaker build_egg
    toymaker build_wininst # on windows only

Rationale
---------

Being able to describe most python packages from a purely static file has the
following advantages:

    * Inspection of packages becomes easier for third parties, like OS
      vendors.
    * No arbitrary code execution, you only have to trust toydist code
      instead of setup.py (which can do anything that python can)
    * Altough the current toydist implementation uses distutils to actually
      build the extensions, distutils becomes an implementation detail of
      the system, in the sense that another build system can be build on
      top of toydist. This gives a simple but powerful way forward for
      improving the situation of python packaging.

Useful discussions which are related to toydist design:

    * BUILDS (never passed the design stage AFAIK):
      http://mail.python.org/pipermail/distutils-sig/2008-October/010343.html
    * Going away from setup.py:
      http://www.mail-archive.com/distutils-sig@python.org/msg08031.html
    * 'Just use debian' on distutils-sig:
      http://mail.python.org/pipermail/distutils-sig/2008-September/010129.html

Toydist design borrows from:

    * Cabal
    * Automake (for data files description) and autoconf
    * RPM spec file

The toydist package indexing is inspired by the Hackage database, CRAN and
linux packaging tools.
