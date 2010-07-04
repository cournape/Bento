===
FAQ
===

Why to create a new tool ?
==========================

Bento is mainly born out of my frustration with distutils while dealing with
complex build issues in NumPy and SciPy. I found distutils poorly documented,
being tightly coupled internally, and inflexible. Other tools built on top only
made it worse by making putting more cruft over distutils instead of fixing it.

I also believe the current solutions suffer a lot of NIH, and ignore all
lessons learned in packaging. Most other language-specific distribution
frameworks (CPAN, CRAN, JSPAN, HackageDB) have some significant features in
common not shared by distutils and setuptools:

    - specified and versioned metadata formats
    - enforced policies
    - separate index of packages (so that you don't need to download a lot
      of software to know the dependencies of a package)
    - simple implementations
    - easy mirroring

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
      extension relies on internal details, and as such are fragile.
    - Extending by inheritence does not work well: when two modules A and B
      extend distutils, it becomes difficult for B to reuse A (for example,
      dealing with setuptools in numpy.distutils extensions has been a constant
      source of bugs).
    - Customizing compilation flags, and more generally some tools involved in
      compilation is too complicated. For example, adding a new tool in the
      build chain requires rewriting the build command, which is aggravated by
      the previous issue. We believe fixing this would end up to rewriting the
      whole thing.
    - Improving distutils to handle dependencies automatically (rebuild only
      the necessary .c files) is difficult because of the way distutils is
      designed (build split across different commands, which may be
      re-executed).
    - The codebase quality is horrible. Subclasses don't share the same
      interface, numerous attributes are added on the fly, etc...

Overall, there is little to save in the current codebase.  Given the relatively
small size of distutils code, the only asset is its "API", but fixing what's
wrong with distutils precisely means breaking the API. As such, a new tool
written from scratch, but taking inspiration of existing tools elsewhere is
much more likely to be an actual improvement.

What about distutils2 ?
=======================

We believe that most efforts in distutils2 are peripherical to the core issues
as described above, and won't improve the situation for the scipy community. We
will implement the distutils-related PEP pushed by the distutils2 team on a
case per case basis.

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

Surely, supporting building extensions on every platform is a huge task ?
=========================================================================

Not really. When I started working on Numscons, a new build system for NumPy
and SciPy based on `SCons`_, supporting C extensions was not very difficult
compared to interactions with distutils.  Numscons is around 2000 LOC (compared
to distutils 10 0000 LOC), and supports most major platforms, including Mac OS
X, Windows 32 and 64 bits, Linux, Free BSD, Solaris, etc... To be fair,
numscons depends on scons itself for some platform peculiarities, but so does
distutils (which relies on autoconf on many platforms through syconfig).

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

The main inspirations for bento current design are taken from:

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
