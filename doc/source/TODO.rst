Here is a non exhaustive list of things to do before bento can be a realistic
alternative to distutils.

TODO:

    - add msi support
    - add proper egg support
    - add mpkg support
    - port stdeb to toydist
    - specify hook mechanism
    - integrate yaku or fbuild
    - add runtime support to install paths
    - test command support
    - distcheck support
    - think about integration with sphinx for doc
    - pre/post hooks for every stage of a typical install
    - integration with at least one real build tool (Scons or waf)
    - avoid cluttering source tree with bento junk
    - handle reliable install/uninstall

Not well thought out yet:
    - pkg_resources: the thing is a giant unmaintainable mess, but can
      we afford ignoring it ?

Milestone
=========

Release 0.0.3
-------------

0.0.3 goals:

    - integrate yaku (without exposing yaku API)
    - put everything in a build directory
    - specify hook mechanism

Release 0.0.4
-------------

0.0.4 goals:

    - test and distcheck support
    - one file distribution

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
