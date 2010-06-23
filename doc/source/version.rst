Version 0.0.3
=============

Not released yet:

    - Renamed from toydist to bento
    - Add hooks to customize arbitrary stages in bento
    - Better command line organization/help
    - Use custom framework for building C extensions, with the
      following features:
        - parallel build support
        - files are automatically rebuilt if they are out of date
          (checksum of the content)
        - designed to be easier to customize (hook based instead of
          subclasses)
        - simple (core ~ 1000 LOC)
    - Hook mechanism: preliminary API to add new commands and
      customize existing ones. A proof of concept of a waf-based build
      command may be found in the examples/hook directory. The API is
      likely to change
    - One file distribution: no need for your users to install any new
      packages, just include one single file into your package to
      build with bento
    - Proof of concept for a distcheck command (to check your
      packaging)
    - Improved documentation

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
