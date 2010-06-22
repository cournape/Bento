Here is a non exhaustive list of things to do before bento can be a realistic
alternative to distutils.

TODO:

    - add msi support
    - add proper egg support
    - namespace packages: how to deal with them (file description and runtime
      support) ?
    - add mpkg support
    - port stdeb to bento
    - specify hook mechanism
    - integrate yaku or fbuild
    - add runtime support to install paths
    - test command support
    - distcheck support
    - think about integration with sphinx for doc
    - pre/post hooks for every stage of a typical install
    - integration with at least one real build tool (Scons or waf)
    - handle reliable install/uninstall

Not well thought out yet:
    - supporting everything that pkg_resources does (resource management
      without __file__ hack, namespace package)

Milestone
=========

Release 0.0.3
-------------

0.0.3 goals:

    - integrate yaku (without exposing yaku API), yaku should have the
      following features:
        - naive // build (extension-based ala waf)
        - ensure it works on windows for simple extensions
    - make sure everything works on python 2.4 -> 2.7
    - make sure everything works on windows

Release 0.0.4
-------------

0.0.4 goals:

    - add basic distutils support
    - specify hook mechanism: document contexts + command flow in bento
    - add tool specification to yaku
    - test and distcheck support
    - rewrite installed-pkg-info mechanism (using json ?)
    - add options to "unbundle" private modules for distribution packagers
    - generate module for data access ($prefix, etc...)

Post 0.0.4
----------

Start working on scipi (nest ?). First proto could be purely static,
file-based. An index easy to parse/update is all we need, really.

Syntax and features of the package description file
===================================================

Missing features:

    - Versioning
    - Multiple libraries
    - Recursive declaration ?
    - Options declaration besides boolean ?
    - Unicode support

Extending the simple build
==========================

    - this is yaku in the short term, maybe something like fbuild in the long
      term

Install-Reinstall-Rebuild-Clean problem
=======================================

Reliable install/reinstall
--------------------------

InstalledPkgInfo should be enough to install/uninstall things, so including it
in installers should be sufficient to get all the data, although it may not be
very efficient.

Fundamental problem: bento vs native packages. Possible solutions:

    1 create a new local site-packages specific to bento, and only use
      bento-enabled package for dependencies:

        - advantages: reliable, relatively simple
        - disadvantages: invasive, requires all dependencies to be
          under bento (in particular numpy/scipy/matplotlib)

    2 try to cope with existing, already installed packages.

        - advantages: no barrier of entry, gradual migration
        - disadvantages: how to do it ?

Scipi
=====

Pypi does not work for the scientific community, so we need to replace it with
our own stack. The goal is something like CRAN:

    - publish a package from sdist with a cabal-like file to scipi
    - the package would be automatically checked for metadata consistency,
      built (included documentation)
    - if the package builds correctly, the package will be available on the
      given platform(s)
    - scipi would have a simple web interface ala CRAN

Technical issues:

    - Simple server for published files (mirrored through rsync). Ideally,
      pure http-based file serving is enough
    - Simple WEB-API to get metadata + files
    - Look at HackageDB in details
