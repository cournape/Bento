===
FAQ
===

Why to create a new tool ?
==========================

Toydist is mainly born out of my frustration with distutils while dealing with
complex build issues in NumPy and SciPy. I found distutils poorly documented,
being tightly coupled internally, and inflexible. Other tools built on top only
made it worse by making putting more cruft over distutils instead of fixing it.

Why not extending existing tools (distutils, etc...) ?
======================================================

There is a general consensus at least in the scientific python community that
distutils is deeply flawed:

    - The design by commands does not make much sense. Each command has its own
      set of options, and getting the options from other commands is difficult,
      if not impossible. For example, the install paths are only known once the
      install command finalize_options has been run, but knowing the
      install prefix at build time is often useful.
    - There is no documentation, and what consitutes public API is not
      documented either. Consequently, every non trivial distutils extension
      relies on internal details, and as such are inherently fragile.
    - Extending by inheritence does not work well: when two modules A and B
      extend distutils, it becomes difficult for B to reuse A (for example,
      dealing with setuptools in numpy.distutils extensions has been a constant
      source of bugs).
    - Customizing compilation flags, and more generally some tools involved in
      compilation is way too complicated. Again, using classes for compilers
      and linkers does not make much sense, as inheritence as an extending
      mechanism does not work well in this situation either. It also makes
      adding new tools in the chain quite difficult.
    - Improving distutils to handle dependencies automatically (rebuild only
      the necessary .c files) is difficult because of the way distutils is
      designed.

Given the relatively small size of distutils code, the only asset is its "API",
but fixing what's wrong with distutils precisely means breaking the API. As
such, a new tool written from scratch, but taking inspiration of existing tools
elsewhere is much more likely to be successfull.

Finally, the current development happening on distutils-sig is mainly the work
of web-developers, who have a different vision of what packaging means.  Most
of their goals are specific to web-development needs, often against known good
practices for packaging.

What are the goals of bento ?
===============================

The main goal of bento is to separate the concerns on building, packaging and
package description, so that it can be easily reused within custom build
frameworks (make, waf, scons, etc...). A simple build system is also provided
so that simple packages do not need to deal with anything besides bento.

Toydist aims at being part of a grander vision for Scientific computing, to
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
distutils (which relies on autoconf on many platforms).

What about existing projects using distutils ?
==============================================

Toymaker, the command line interface to bento, contains an experimental
command to convert existing setup.py to bento format.

I also believe it is possible to support most distutils/setuptools features in
bento file format, and convert a package description to a
distutils/setuptools Distribution instance. As conversion from bento to
distutils would be much easier to do reliably than the contrary, it could be
used as a transition, so that packages who have heavily invested in distutils
can still use distutils extensions.

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
