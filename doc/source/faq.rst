===
FAQ
===

Why to create a new tool ?
==========================

Because scientific code depends so much on compiled languages (C and Fortran),
the scipy community had to significantly extend distutils. It was found to be
more and more difficult to maintain, and the source of numerous user
complaints. In the last decade, several attemps of refactoring distutils and
our extensions have been made, but none succeeded.

Bento is born out of this experience. We also believe that current solutions
based on distutils suffer a lot of NIH, and ignore lessons learned in packaging
in most other systems.  Bento aims at shamelessly copying what works in other
systems (CPAN, CRAN, JSAN, HackageDB).

What are the goals of bento ?
=============================

The main goal of bento is to separate the concerns on building, packaging and
package description, so that it can be easily reused within custom build
frameworks (make, waf, scons, etc...). A simple build system is also provided
so that simple packages do not need to deal with anything besides bento.

Bento aims at being part of a grander vision for Scientific computing, to
make something like CRAN available to python users.  By being simpler, more
explicit, it is hoped that bento will make the development of a
scientific-specific Pypi easier.

Why not extending existing tools (distutils, etc...) ?
======================================================

There is a general consensus at least in the scientific python community that
distutils is deeply flawed:

    - The design by commands does not make much sense. In distutils, each
      command has its own set of options, and getting the options from other
      commands is difficult, if not impossible. For example, the install paths
      are only known once the install command finalize_options has been run,
      but knowing the install prefix at build time is often useful.
    - There is no developer documentation, and what consitutes public API is
      not documented either. Consequently, every non trivial distutils
      extension relies on internal details, and as such is fragile.
    - Extending by inheritence does not work well: when two modules A and B
      extend distutils, it becomes difficult for B to reuse A (for example,
      dealing with setuptools in numpy.distutils extensions has been a constant
      source of bugs).
    - Customizing compilation flags, and more generally some tools involved in
      compilation is too complicated. For example, adding a new tool in the
      build chain requires rewriting the build command, which is aggravated by
      the previous issue. We believe fixing this would end up in rewriting the
      whole thing.
    - Improving distutils to handle dependencies automatically (rebuild only
      the necessary .c files) is difficult because of the way distutils is
      designed (build split across different commands, which may be
      re-executed).
    - The codebase quality is horrible. Subclasses don't share the same
      interface, numerous attributes are added on the fly, etc...

Overall, there is little to save in the current codebase. At least all of the
command and ccompiler code must go away, and that's already 2/3 of distutils
code.  Given the relatively small size of distutils code, the only asset is its
"API", but fixing what's wrong with distutils precisely means breaking the API.
As such, a new tool written from scratch, but taking inspiration of existing
tools elsewhere is much more likely to be an actual improvement.

One should note that numpy's extensions to distutils are pretty big:
numpy.distutils itself is as big as distutils in term of code size, and is the
biggest user of distutils API as far as I know.  Hence, we are well aware of
the cost of a total break from distutils.

What about distutils2 ?
=======================

We believe that most efforts in distutils2 are peripherical to our core issues
as described above, and won't improve the situation for the scipy community.
History-wise, it should also be noted that Bento precedes distutils2 by a
couple of months (the first prototype was announced during my talk at scipy
India in december 2009).

Starting from the distutils codebase is not very appealing, as most of it would
need to be scrapped (at least the whole command and compiler business needs to
be completely rewritten). There are also irreconcilable differences on some
key points. In particular, we think the following features are essential:

    1. specified and versioned metadata formats, instead of implementation
       specific data
    2. enforced packaging policies (version, required metadata, etc...)
    3. separate index of packages (so that you don't need to download a lot
       of software to know the dependencies of a package)
    4. easy mirroring (ideally file based)
    5. simple implementations

Although controversial in the python community, there is a large consensus
within the scipy community on those points.  Some of them have been rejected by
various distutils2 members (2, 3 and 4 in particular), and we are unwilling to
compromise on them. Distutils-related PEPs pushed by the distutils2 team will
be implemented on a case per case basis (some of them are obsolete as far as
bento is concerned, in the sense that they are already implemented, if only in
intent).

Moreover, as bento is designed from the ground up to be split into mostly
independent parts, it is possible to reuse its code in other projects. No
effort will be made to tie some features to bento to force people to use it.
If bento ends up being an experiment into useful new APIs integrated into
distutils2, bento would be considered successful. If our vision ends up being
wrong or unreachable, some of the code should be useful nonetheless.

Isn't it too difficult to support building extensions on every platform ?
==========================================================================

People often assume that distutils has a lot of platform-specific knowledge, in
particular to build C extensions. Except for a few exceptions (mostly on
non-Unix platforms), most of this knowledge actually comes from autoconf
through the sysconfig module.

Any non-superficial modification of the C compilation part of distutils will
also require reworking the platform-specific knowledge anyway.

What about existing projects using distutils ?
==============================================

Bentomaker, the command line interface to bento, contains an experimental
command to convert existing setup.py to bento format.

I also believe it is possible to support most distutils/setuptools features in
bento file format, and convert a package description to a distutils/setuptools
Distribution instance. It could be used as a transition, so that packages who
have heavily invested in distutils can still use distutils extensions: the
metadata would be described in a bento.file, but distutils would still drive
the build and installation.

Is bento based on existing tools ?
====================================

The main inspirations for bento's current design are taken from:

    - `Cabal`_, the packaging tool for Haskell: the bento file format is
      mainly an adaptation of Cabal to python.
    - `Autoconf`_, for the flexible install scheme, automake's way of declaring
      extra distribution files (data files).
    - `RPM`_, for the spec file format.
    - Setuptools: exe-based script generation on windows, egg format

.. _RPM: http://rpm5.org/docs/api/specfile.html
.. _Cabal: http://www.haskell.org/cabal
.. _Scons: http://www.scons.org
.. _Autoconf: http://sources.redhat.com/autobook/

Who are the authors of bento ?
==============================

Currently, I (David Cournapeau) am the main author of bento. I am a core
contributor to Numpy and Scipy, and have been the main maintainer of Numpy
distutils extensions for more than two years. I am also an occasional
contributor to scons (a make replacement in python), and debian packager.

Other contributors:
    - Stefan Van der Walt: initial implementation of the bento.info parser
    - Philip J. Eby: for answering most of my questions about
      setuptools/eggs design

What are the main features of bento compared to its competitors
===============================================================

Bento has the following main features:
    - Full static metadata description for simple packages
    - Arbitrary extensibility through python scripts
    - Reliable build and installation: no more stalled files when installing,
      out-of-date source files and dependencies automatically detected for C
      extensions

The following features are being implemented as well:
    - Optional recursive package description for complex packages
    - Easy customization of compilation flags and toolchain
    - Robust command dependencies from dependencies descriptor: no more
      monkey-patching nonsense to insert a new command between two existing
      subcommands 
    - The build process may be replaced by make, waf or scons if desired, while
      still keeping the installation and packaging features of bento (windows
      installers, eggs, etc...)
    - New packaging format which can be translated to any existing one if
      wanted (egg, wininst, msi, etc...). The format is optimized for
      installation
    - Reliable uninstallation
