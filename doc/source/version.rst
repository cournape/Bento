Version 0.0.6
=============

Released on .
Main features:

    - Preliminary support for .mpkg (Mac OS X native packaging)
    - More consistent API for extension/compiled library build registration
    - Build directory is now customizable through bentomaker with
      --build-directory option
    - Out of tree builds support (i.e. running bento in a directory which does
      not contain bento.info), with global --bento-info option
    - More reliable distutils compatibility layer

Internals
---------

    - Significantly better code coverage of bento commands.
    - Use node-based representation of package description in build and install
    - Cleanly separated source, cwd and build directories
    - Rewrote distutils compatibility layer to use command contexts.
      Concretely, this means it works much closer to how bentomaker does, so
      there should be less surprises between bentomaker and distutils
      execution.

Version 0.0.5
=============

Released on 8th March 2011. This is mostly a stabilization of features
implemented so far, with some code refactoring to enable easier customization
of the build process.  Main features:

    - All python versions from 2.4 up to 3.1 now pass the test suite (3.2 will
      follow once the distribute issue with 3.2 is fixed)
    - If run under a virtual environment (virtualenv), bento will install the
      package inside the virtualenvironment by default
    - When a command depends on other commands, those are now automatically
      run, e.g.::

        bentomaker build_egg # automatically run configure and build

    - Update to last yaku, which contains a lot of improvements (too many to
      list here)
    - Add --list-files option to install command to list files to be installed
    - Add --transaction option to install to produce a "transaction log". The
      transaction log will enable rollback (a first step towards reliable
      uninstall). 
    - Internal changes to enable easier change of build tool (a waf-based
      example for simple extensions is available for waf 1.6.x)
    - Added experimental distutils compatibility layer so that one can write a
      setup.py which will pick up all information from bento.info. This enables
      projects using bento to still be able to use tools such as pip.

Internals
---------

    - Commands are now registered to a single global command registry
    - Commands are now run with a command-specific context, which can be
      extended for further customization (e.g. waf support in the build stage).
    - Command dependency is now handled dynamically: order is set outside
      command class definition, and order resolution is done at runtime with a
      simple topological sort on the dependency order.

Version 0.0.4
=============

Released on 9th October 2010. Main features:

    - Add ConfigPy option to produce a simple config_py module. At the
      moment, this module may be used to access installed data at
      runtime without __file__ hack.
    - Add 'not flag(flag_name)' and 'not true|false' to the bento.info
      grammar
    - Add --with-bundling option to disable bundling of
      ply/yaku/simplejson to ease packaging for OS vendors
    - Recursive bento and hook files for complicated, nested packages
      (scipy, twisted)
    - Numerous features to build numpy and scipy - experimental bento-based
      build branches for both are available on http://github.com/cournape
      (_bento_build branches)

Version 0.0.3
=============

Released on 2th July 2010. Main features:

    - Add hooks to customize arbitrary stages in bento
    - Parallel and reliable build of C extensions through yaku build
      library.
    - One file distribution: no need for your users to install any new
      packages, just include one single file into your package to
      build with bento
    - Improved documentation
    - 2.4 -> 2.7 support

Toydist renamed to bento
------------------------

Bento means lunchbox in Japanese. Bento are often well packaged, and
this software aims at doing the same for your python package.

Hook mechanism
--------------

It is now possible to override some bento commands with a hook file
which is just a python script. Although not well documented yet, it
should enable complex customization, like interfacing with a build
system (waf, scons, make), dynamically modify the package content,
etc... the examples/hooks directory contains a few simple examples.

Yaku, build mini-framework
--------------------------

In version 0.0.2, bento still depended on distutils internally to
build extensions. Bento now uses yaku, a mini build framework. Yaku
main features are:

    - File content-based tracking: if a file content is changed, it is
      automatically rebuild
    - Environment changes detection: if the compilation options
      change, the files are automatically rebuilt
    - Multiple jobs execution (experimental)
    - Easily customizable

It should noted that bento was conceived to be agnostic to the
build system, and will remain so. In particular, projects with complex
build issues are advised to use make, scons or waf. Future versions of
bento will contain helpers for some of those tools.

One file distribution
---------------------

Bento now includes a one file distribution of itself, so that you only
need to include that one file in your project to use bento. The file
weights ~350 kb, and can be reduced to ~80 kb if you don't need to
include windows binary installer support.

Improved command line interface
-------------------------------

Internal changes:

    - Lots of internal cleaning
    - Replace hackish custom format by json for build manifest
    - Heavily refactor installed package description API
    - All the installers (install, egg and wininst buidlers) now share
      most of their implementation

Version 0.0.2
=============

Released on the 22th April 2010:

    - Ply-based parser with (relatively) sane grammar
    - Windows installers and eggs building support

Version 0.0.1
=============

Unreleased, presented at Scipy India in December 2009.
