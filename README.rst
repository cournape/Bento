.. image:: https://secure.travis-ci.org/cournape/Bento.png
    :alt: Travis CI Build Status

Bento is an alternative to distutils-based packaging tools such as distutils,
setuptools or distribute. Bento focus on reproducibility, extensibility and
simplicity (in that order).

Packaging is as simple as writing a bento.info file with a file which looks as
follows::

    Name: Foo
    Author: John Doe

    Library:
        Packages: foo

The package is then installed with bentomaker, the command line interface to
bento::

    bentomaker install

Installing
==========

To install bento, you can either:

    * install bento from itself (recommended)::

        python bootstrap.py
        ./bentomaker install

    * install bento using setuptools (not recommended)::

        python setup.py install

Python3 support
---------------

Bento supports python 3 as is, so there is no need to run 2to3 on it (doing so
will probably break it).

Development
============

Bento discussions happen on the bento Mailing list (bento@librelist.com,
archive on `bento-ml`_). To subscribe, you simply need to send an email to the
list. Development is on `github`_. Bugs should be reported on bento
`issue-tracker`_. Online `documentation`_ is available on github as well.

Why you should use bento ?
==========================

    * Straightfoward package description, in an indentation-based syntax
      similar to python
    * Simple packages can have their setup.py automatically converted through
      the 'convert' command
    * Distutils compatibility mode so that a bento package can be installed
      through pip
    * Adding new commands is simple
    * Pluggable build-backend: you can build your C extensions with a real
      build system such as waf or scons.
    * Easy to customize install paths from the command line, with sensible
      defaults on every platform
    * Installing data files such as manpages, configuration, etc... is
      straightforward and customizable through the command line
    * Supports all python versions >= 2.4 (including 3.x)
    * Designed with reproducibility in mind: re-running the same command twice
      should produce the same result (idempotency)
    * Preliminary support for windows installers (.exe), eggs and mpkg.

But bento does more:

    * Designed as a library from the ground up, with a focus on robustness and
      extensibility:

        * new commands can be inserted before/after an existing one without
          modifying the latter (no monkey-patching needed)
        * easy to add command line options to existing commands
        * each command has a pre/post hook
        * API designed such as commands need to know very little from each other.
        * Moving toward a node-based architecture for robust file location
          (waf-based design)
        * No global variable/singleton in bento itself

    * Easily bundable, one-file distribution to avoid extra-dependencies when
      using bento. You only need to add one file to your sources, no need for
      your users to install anything.
    * Basic support for console scripts ala setuptools
    * Dependency-based extension builders (source content change is
      automatically rebuilt)
    * Parallel build support for C extensions
    * Low-level interface to the included build tool to override/change any
      compilation parameter (compilation flag, compiler, etc...)

Planned features:

    * Reliable and fast (parallel) 2->3 convertion.
    * Support for msi packages
    * Reliable conversion between packaging formats on the platforms where it
      makes sense (egg <-> wininst, mpkg <-> egg, etc...)
    * Provide API to enable Linux distributors to write simple extensions for
      packaging bento-packages as they see fit
    * Infrastructure for a correctly designed package index, using
      well-known packaging practices instead of the broken easy_install + pypi
      model (easy mirroring, enforced metadata, indexing to enable
      querying-before-installing, reliable install, etc...).

WHILE BENTO IS ALREADY USABLE, IT MAY STILL SIGNIFICANTLY CHANGE IN BACKWARD
INCOMPATIBLE WAYS UNTIL THE FIRST ALPHA.

.. _github: http://github.com/cournape/Bento.git
.. _issue-tracker: http://github.com/cournape/bento/issues
.. _documentation: http://cournape.github.com/Bento
.. _bento-ml: http://librelist.com/browser/bento
