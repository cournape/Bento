Here is a non exhaustive list of things to do before bento can be a realistic
alternative to distutils.

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

    - Simple build framework with dependency handling
    - Pre/Post hooks for every stage of a typical install
    - Integration with at least one real build tool (Scons or waf)
    - Avoid cluttering source tree with bento junk
    - Integration with sphinx
    - Implement a distcheck-like command
    - Handle reliable install/uninstall

Install-Reinstall-Rebuild-Clean problem
=======================================

Reliable builds
---------------

For complex packages, the solution is clearly make/scons/waf/etc....

For simple packages, one needs something simpler:
    
    - How hard would it be to have dependency handling in bento ?
    - Do we need full dependency ? Since it would arguably used for simple
      problems, brute force may be considered. For example, one could
      always install, byte-compile everything from scratch, and only do
      dependency handling for build

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
