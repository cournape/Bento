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

To install bento for python 3::

    python bootstrap.py # this should be run under a supported python 2.x version
    ./bentomaker run_2to3
    # Not mandatory: sanity check of the converted code
    ./bentomaker test_py3k

and follows the given instructions.

Main Features
=============

    * Package description in a simple, indentation-based format. Supports most
      distutils/setuptools metadata as well as packages and extensions.
      Recursive support for deeply-nested packages.
    * Supports all python versions >= 2.4 (including 3.x)
    * Convert command to create a bento package from a setup.py
    * Distutils compatibility mode so that a bento package can be installed
      through pip
    * Designed with reproducibility in mind: re-running the same command twice
      should produce the same result (idempotency)
    * Easy to customize install paths from the command line, with sensible
      defaults on every platform
    * Preliminary support for windows installers (.exe), eggs and mpkg.
    * Pluggable build backend, so that one can use an advanced build tool such
      as waf to build complex C extensions.

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

    * Support for msi packages
    * Reliable conversion between packaging formats on the platforms where it
      makes sense (egg <-> wininst, mpkg <-> egg, etc...)
    * Provide API to enable Linux distributors to write simple extensions for
      packaging bento-packages as they see fit
    * Infrastructure for a correctly designed package index, using
      well-known packaging practices instead of the broken easy_install + pypi
      model (easy mirroring, enforced metadata, indexing to enable
      querying-before-installing, reliable install, etc...).

Bento discussions happen on the bento Mailing list (bento@librelist.com,
archive on `bento-ml`_), and development is on `github`_. Bugs should be
reported on bento `issue-tracker`_. Online `documentation`_ is available on
github as well.

WHILE BENTO IS ALREADY USABLE, IT MAY STILL SIGNIFICANTLY CHANGE IN BACKWARD
INCOMPATIBLE WAYS UNTIL THE FIRST ALPHA.

.. _github: http://github.com/cournape/bento.git
.. _issue-tracker: http://github.com/cournape/bento/issues
.. _documentation: http://cournape.github.com/bento
.. _bento-ml: http://librelist.com/browser/bento
