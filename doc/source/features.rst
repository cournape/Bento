Features
========

The main features of toydist are:

* Package descriptions are done in a declarative file (inspired from Cabal_ and
  RPM_ .spec files), so you can easily introspect basic features of packages
  without running any python code (besides toydist).
* Include toymaker, a command line interface to configure, build, install
  projects.
* Easy integration with native filesystem conventions: every install directory
  is customizable at the configure stage (autoconf-inspired).
* Building eggs does not require depending on setuptools anymore.

Future features
---------------

* Simple C-extension building framework to cut distutils dependency
* Scons/waf libraries to interact with Scons_ and Waf_ build tools
* Hooks for customizing arbitrary stages

Inspirations
------------

The main initial inspiration for toydist was Cabal_, the packaging tool used in
the Haskell community.

I have also "stole" (or intend to steal) features from other similar solutions:

    * Autotools: flexible install scheme (autoconf), extra files installation (automake)
    * SCons/Waf: tool design, mini build framework
    * Setuptools: exe-based script generation on windows, egg format

.. _RPM: http://rpm5.org/docs/api/specfile.html
.. _Cabal: http://www.haskell.org/cabal
.. _Scons: http://www.scons.org
.. _Waf: http://code.google.com/p/waf
