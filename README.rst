An experimental alternative to distutils/setuptools/etc...

Toydist discussion happen on NumPy Mailing list, and development is on
`github`_. Bug should be reported on toydist `issue-tracker`_. Online
`documentation`_ is available on github as well

.. _github: http://github.com/cournape/toydist.git
.. _issue-tracker: http://github.com/cournape/toydist/issues
.. _documentation: http://cournape.github.com/toydist

Quick start
-----------

From existing setup.py
~~~~~~~~~~~~~~~~~~~~~~

toymaker, the toydist command line interface has an experimental convert
command to convert existing setup.py::

    toymaker convert

If successfull, it will write a file toysetup.info. If it fails, convert.log
should contain useful information.

From scratch
~~~~~~~~~~~~

A simple python distribution named hello, with one package hello::

    hello/__init__.py
    hello/...

may be described as follows::

    Name: hello
    Version: 1.0

    Library:
        Packages:
            hello

Note that for now, you *have* to use 4 spaces for indentation, always. This is
an arbitrary limitation which will be removed at some point once the parser is
improved.

Building, installing
~~~~~~~~~~~~~~~~~~~~

Assuming the file is named toysetup.info, the command line interface toymaker
can be used to configure, build, install, etc... the distribution::

    toymaker configure --prefix=/usr/local
    toymaker build
    toymaker install
    toymaker sdist

What can it do
--------------

Not much ATM. The following is implemented:

    * Basic library to parse the static format. The format support the
      following:

        * Most (all?) metadata from PKG-INFO format 1.2
        * Command line options for additional path and flags
        * One simple way to deal with installed data files
        * One simple wat to deal with non-installed data (e.g. only
          included in sdist)
        * Packages, modules and simple C extensions

    * Building and installing simple packages from the static
      format (Linux and Mac OS X only for now), sdist generation
    * Experimental automatic convertion of existing setup.py to a new
      static format
    * Basic egg generation

Rationale
---------

Being able to describe most python packages from a purely static file has the
following advantages:

    * No arbitrary code execution, you only have to trust toydist code
      instead of setup.py (which can do anything that python can)
    * Inspection of packages becomes easier for third parties, like OS
      vendors.
    * Also the current toydist implementation uses distutils to actually
      build the extensions, distutils becomes an implementation detail of
      the system, in the sense that another build system can be build on
      top of toydist. This gives a simple but powerful way forward for
      improving the situation of python packaging.

Useful discussions which are related to toydist design:

    * BUILDS (never passed the design stage AFAIK):
      http://mail.python.org/pipermail/distutils-sig/2008-October/010343.html
    * Going away from setup.py:
      http://www.mail-archive.com/distutils-sig@python.org/msg08031.html
    * 'Just use debian' on distutils-sig:
      http://mail.python.org/pipermail/distutils-sig/2008-September/010129.html
