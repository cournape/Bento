Version 0.0.3
=============

Not released yet. Main features:

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
