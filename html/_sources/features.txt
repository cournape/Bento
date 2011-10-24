Features
========

Main features currently implemented
-----------------------------------

* Package are described in a declarative file (inspired from Cabal_ and
  RPM_ .spec files), so you can easily introspect basic features of packages
  without running any python code (besides bento).
* A command line interface to configure, build, install projects.
* Easy integration with native filesystem conventions: every install directory
  is customizable at the configure stage (autoconf-inspired).
* Building eggs without depending on setuptools.
* Simple C-extension building framework, with content-based automatic
  dependency tracking, and parallel build support.
* Recursive package description support
* Hooks for customizing arbitrary stages (configure, build, etc...)
* Easy to implement new commands
* Windows installer support and basic egg support.

Future features
---------------

* Scons/waf libraries to interact with Scons_ and Waf_ build tools, so
  that complex packages can have access to a real build system with
  dependencies handling.
* Conversion to native packages (.deb, .rpm, .msi, etc...)

.. _RPM: http://rpm5.org/docs/api/specfile.html
.. _Cabal: http://www.haskell.org/cabal
.. _Scons: http://www.scons.org
.. _Waf: http://code.google.com/p/waf
