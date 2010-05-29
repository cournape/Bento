Features
========

Main features currently implemented
-----------------------------------

* Package descriptions are done in a declarative file (inspired from Cabal_ and
  RPM_ .spec files), so you can easily introspect basic features of packages
  without running any python code (besides bento).
* A command line interface to configure, build, install projects.
* Easy integration with native filesystem conventions: every install directory
  is customizable at the configure stage (autoconf-inspired).
* Building eggs without depending on setuptools.

Future features
---------------

* Simple C-extension building framework to cut distutils dependency
* Scons/waf libraries to interact with Scons_ and Waf_ build tools, so that
  complex packages can have access to a real build system with dependencies
  handling.
* Hooks for customizing arbitrary stages (configure, build, etc...)
* Conversion to native packages (.deb, .rpm, .exe, .msi, etc...)

.. _RPM: http://rpm5.org/docs/api/specfile.html
.. _Cabal: http://www.haskell.org/cabal
.. _Scons: http://www.scons.org
.. _Waf: http://code.google.com/p/waf
