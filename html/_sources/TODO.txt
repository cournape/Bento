====
TODO
====

Here is a non exhaustive list of things to do for a 1.0 release.

TODO:

    - make bento+waf bundable (make it possible to bentofy a package with a
      single file)

        - needs bento.info versioning

    - add 2to3 command
    - think about integration with sphinx for doc
    - test command support
    - specify hook mechanism
    - add msi support
    - add proper egg support
    - namespace packages: how to deal with them (file description and runtime
      support) ?
    - port stdeb to bento
    - handle reliable install/uninstall
    - fix messy lexer/parser code

Not well thought out yet:
    - supporting everything that pkg_resources does (namespace
      package), except multiple-version installs.

Syntax and features of the package description file
===================================================

The parser and lexer need to be seriously cleaned-up.

Missing features:

    - Format-Versioning
    - Options declaration besides boolean ?
    - Unicode support

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
