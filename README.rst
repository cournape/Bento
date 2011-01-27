A pythonic, no-nonsense packaging tool for python software. Packaging is as
simple as writing a bento.info file with a file which looks as follows::

    Name: Foo
    Author: John Doe

    Library:
        Packages: foo

The package is then installed with bentomaker, the command line interface to
bento::

    bentomaker configure
    bentomaker build
    bentomaker install

The main features of bento are:

    * Static package description which can be queried without running any
      python code
    * Support for arbitrary installation scheme (ala autoconf, with sensible
      defaults on Windows)
    * Simple and flexible data files installation description: you can tell
      bento to install any file anywhere, without the need to harcode any
      installation path in the package description.
    * Hooks to complement or override commands. Hooks provide access to most
      key data of the package, to enable powerful customization. A proof of
      concept overriding the build command to build C extensions with waf is
      provided.
    * Dependencies between commands is not harcoded in the command themselves,
      but are specified externally in a directed acyclic graph. This will
      enable customization of commands without typical hacks seen in distutils
      and its successor, where you need to monkey patch things just to make
      your command run in the right order.

But bento does more:

    * Easily bundable, one-file distribution to avoid extra-dependencies when
      using bento. You only need to add one file to your source tarball !
    * Automatic conversion from setup.py to bento format
    * Basic support for console scripts ala setuptools
    * Preliminary support for building eggs and windows installers
    * Dependency-based extension builders (source content change is
      automatically rebuilt)
    * Parallel build support for C extensions
    * Low-level interface to the included build tool to override/change any
      compilation parameter (compilation flag, compiler, etc...)
    * Optionally generate a python module with all installation paths to avoid
      relying on __file__ to retrieve resources.

The goals of bento are simplicity and extensibility. There should be only one
way to package simple packages (ideally, relying only on the bento.info
file), while being flexible enough to handle complex softwares. The ultimate
goal of bento is to replace the hideous distutils extensions to build NumPy
and SciPy, and enable reliable installation of scikits and other scientific
python packages.

Planned features:

    * Support for msi and Mac OS X .mpkg
    * Reliable conversion between packaging formats on the platforms where it
      makes sense (egg <-> wininst, mpkg <-> egg, etc...)
    * Provide API to enable Linux distributors to write simple extensions for
      packaging bento-packages as they see fit
    * Distutils compatibility mode, driven by the bento.info file
    * Protocol to integrate with real build tools like scons, waf or
      make
    * Infrastructure for a correctly designed package index, using
      well-known packaging practices instead of the broken easy_install + pypi
      model (easy mirroring, enforced metadata, indexing to enable
      querying-before-installing, reliable install, etc...).

Code-wise, bento has the following advantages:

    * Clear separation of intent between package description, configuration,
      build and installation
    * No dependency on distutils or setuptools code, with a focus on
      using standard python idioms

Bento discussion happen on NumPy Mailing list, and development is on
`github`_. Bugs should be reported on bento `issue-tracker`_. Online
`documentation`_ is available on github as well.

BENTO IS IN (VERY) EARLY STAGES: ANY PRODUCTION USAGE IS STRONGLY DISCOURAGED
AT THIS POINT.

Nevertheless, bento is already capable of building numpy and scipy on some
platforms, with less code and more flexibility than the current distutils-based
extensions.

.. _github: http://github.com/cournape/bento.git
.. _issue-tracker: http://github.com/cournape/bento/issues
.. _documentation: http://cournape.github.com/bento

Installing bento
------------------

Bento may be installed the usual way from setup.py::

    python setup.py install --user # python 2.6 and later
    python setup.py install --prefix=some_directory

Alternatively, there is a bootstrap script so that bento can install itself::

    python bootstrap.py # create the bentomaker[.exe] script/executable 
    ./bentomaker configure && ./bentomaker build && ./bentomaker install

Quick starting guide for packaging with bento
-----------------------------------------------

From existing setup.py
~~~~~~~~~~~~~~~~~~~~~~

bentomaker, the bento command line interface has an experimental convert
command to convert existing setup.py::

    bentomaker convert

If successfull, it will write a file bento.info. If it fails,
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

Bento currently only has a command-line interface, bentomaker. It can be used
to configure, build, install, etc... the distribution::

    bentomaker configure --prefix=/usr/local
    bentomaker build
    bentomaker install
    bentomaker sdist
    bentomaker build_egg
    bentomaker build_wininst # on windows only

Regenerating the one-file distribution file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you modify any source file, you need to regenerate the one-file
distribution::

    python tools/singledist.py

If you don't want to include windows executables (e.g. you don't support
windows)::

    python tools/singledist --noinclude-exe

Rationale
---------

Being able to describe most python packages from a purely static file has the
following advantages:

    * Inspection of packages becomes easier for third parties, like OS
      vendors.
    * No arbitrary code execution for simple packages, you only have to trust
      bento code instead of setup.py (which can do anything that python can)
    * Although the current bento implementation uses distutils to actually
      build the extensions, distutils becomes an implementation detail of the
      system, in the sense that another build system can be build on top of
      bento. This gives a simple but powerful way forward for improving the
      situation of python packaging.

Useful discussions which are related to bento design:

    * BUILDS (never passed the design stage AFAIK):
      http://mail.python.org/pipermail/distutils-sig/2008-October/010343.html
    * Going away from setup.py:
      http://www.mail-archive.com/distutils-sig@python.org/msg08031.html
    * 'Just use debian' on distutils-sig:
      http://mail.python.org/pipermail/distutils-sig/2008-September/010129.html

Bento design borrows from:

    * Cabal
    * Automake (for data files description) and autoconf
    * RPM spec file

The bento package indexing is inspired by the Hackage database, CRAN and
linux packaging tools.
