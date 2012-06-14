Version 0.2
===========

Released on .

Version 0.1
===========

Released on 12th June 2012.

Main features:

        - new commands register_pypi and upload_pypi to register a package to
          pypi and upload tarballs to it.
        - waf backend: cython tool automatically loaded if cython files are
          detected in sources
        - UseBackends feature: allows to declare which build backend to use
          when building C extensions in the bento.info file directly
        - add sphinx command to build a package documentation if it uses
          sphinx.
        - add tweak_library/tweak_extension functions to build contexts to
          simplify simple builder customization (e.g. include_dirs, defines,
          etc...)
        - add simpler API to register output nodes
        - add --use-distutils-flags configure option to force using flags from
          distutils (disabled by default).
        - add --disable-autoconfigure build option to bypass configure for fast
          partial rebuilds. This is not reliable depending on how the
          environment is changed, so one should only use this during
          development.
        - add register_metadata API to register new metadata to be filled in
          MetaTemplateFile
        - Deprecate MetaTemplateFile, and use MetaTemplateFiles instead to
          allow for multiple template files

Fixed issues
------------

Internals
---------

        - Test coverage has been significantly improved
        - Lots of code style fixes to make the codebase more consistent
        - build backend-specific code has been moved to bento.backends
        - parser code has been moved to bento.parser
        - last hook-related global variables have been removed
        - bentomaker itself does not use global variables anymore for either
          caching or command/context/option registration
        - add backend concept: a backend knows how to register itself, to avoid
          having to register command, context and options contexts separately

Version 0.0.8.1
===============

Released on .

Bugfix release

Fixed issues
------------

    - python 2.4-ism
    - fix in-place build/bootstrap issues for bento itself

Version 0.0.8
=============

Released on 26th March 2012.

While this release does not have big user-visible features, it brings lots of
internal improvements and bug fixes, especially for the convert command.

Main features:

    - Path sections can now use conditionals
    - More reliable convert command to migrate
      distutils/setuptools/distribute/distutils2 packages to bento
    - Single-file distribution can now include waf itself
    - Nose is not necessary to run the test suite anymore
    - Significant improvements to the distutils compatibility layer
    - LibraryDir support for backward compatibility with distutils packages
      relying on package_dir feature

Fixed issues
------------

    - Running bento for python 2.x after having run it for 3.x does not crash
      bento anymore
    - Using bento installed as root should now work (#46). This is still not
      recommended, though

Internals
---------

    - move most global state from bento into bentomakerlib
    - add basic end-to-end tests for bento.distutils
    - bento.distutils simplified: it is going toward a "shell" around bento
      with compatibility with pip/easy_install/virtualenv and away from a
      distutils extension
    - six is now used to handle most 2/3 compatibilities.
    - convert-related code is now in its won package, and has some decent
      functional tests for basic features.

Version 0.0.7
=============

Released on 25th October 2011.

Main features:

    - New bento.info fields:
        - 'DescriptionFromFile': pointer to a file to read description from.
        - 'Keywords' metadata field
        - 'MetaTemplateFile': pointer to template files to be filled with bento
          metadata
    - Support for DESTDIR-like feature to ease downstream packaging
    - Comment support in bento.info
    - Sdist now has a format option, and supports zip archive as well
    - Builders in waf context now support arbitrary customization
    - python 2 and 3 are supported from the same codebase to avoid
      bootstrapping issues.

Fixes:

    - fix handling of customized flags when getting cached package information
    - fix classifier handling

Version 0.0.6
=============

Released on 13th July 2011.

Main features:

    - Preliminary support for .mpkg (Mac OS X native packaging)
    - More consistent API for extension/compiled library build registration
    - Build directory is now customizable through bentomaker with
      --build-directory option
    - Out of tree builds support (i.e. running bento in a directory which does
      not contain bento.info), with global --bento-info option
    - Completely revamped distutils compatibility layer: it is now a thin layer
      around bento infrastructure, so that most bento packages should be
      pip-installable, while still keeping bento customization capabilities.
    - Hook File can now be specified in recursed bento.info

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
