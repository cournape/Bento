========================================================
Transition from existing python packaging infrastructure
========================================================

Even if you are convinced than bento is more appropriate for your needs than
current distutils-based tools, there is a significant hurdle to transition to a
new infrastructure for your package. First, you need to convert your package,
but you also potentially loose goodies such a putting your package on pypi, or
being installable through tools such as pip or easy_install.

Ideally, such tools would become pluggable so that they can be made aware of
new packaging formats, but in the mean-time, the practical approach of bento is
to "emulate" distutils just enough to make them work with the most useful bits
of the current python packaging infrastructure, and to provide tools to convert
existing setup.py to the bento format.

Converting distutils-based packages
===================================

The bentomaker command-line tool has a convert command which should be run at
the top of your source tree (the directory containing your top setup.py).
Because the convert command works by running the setup.py, you need to make
sure you can run the setup.py. To convert your package, just do::

    bentomaker convert

If successfull, this will write a bento.info file whose content has been pulled
of the convert command analysis (it will not overwrite an existing one). It
first tries to determine whether your setup.py uses setuptools or not, and then
run it with mocked distutils objects for the actual conversion.  Since the
convert command works by inserting various hooks into distutils internals, it
is inherently fragile. 

It will definitely not work in the following cases:

    * you use the package_dir feature: bento does not support the feature at all.
    * you have your own distutils extensions (setuptools and numpy.distutils
      are somehow handled, though, and other common distutils extensions may be
      added as well).

It should support the following features:

    * All the distutils metadata
    * Some setuptools metadata (like require or console scripts)
    * module, packages and extensions
    * data files as specified in data_files
    * source files in MANIFEST[.in]

Note:: because the convert command does not parse the setup.py, but runs it
instead, it only handles package description as defined by this one run of
setup.py. For example, bento convert cannot automatically handle the following
setup.py::

    import sys
    from setuptools import setup

    if sys.platform == "win32":
        requires = ["sphinx", "pywin32"]
    else:
        requires = ["sphinx"]

    setup(name="foo", install_requires=requires)

If run on windows, the generated bento.info will be::

    Name: foo

    Library:
        InstallRequires:
            pywin32,
            sphinx

and::

    Name: foo

    Library:
        InstallRequires:
            sphinx

otherwise.

Note:: bento syntax supports simple conditional, so after conversion, you
could modify the generated file as follows::

    Name: foo

    Library:
        InstallRequires:
            sphinx
        if os(win32):
            InstallRequires:
                pywin32

Adding bento-based setup.py for compatibility with pip, etc...
==============================================================

Although nothing fundamentally prevents bento to work under installers such as
pip, pip currently does not know anything about bento. To help transition,
bento has a distutils compatibility layer. A setup.py as simple as::

    import setuptools
    import bento.distutils
    bento.distutils.monkey_patch()

    from setuptools import setup

    if __name__ == '__main__':
        setup()

will enable commands such as::

    python setup.py install
    python setup.py sdist

to work as expected, taking all the package information from bento.info file.
Note that the monkey-patching done by bento.distutils on top of setuptools is
explicit - solely importing bento.distutils will not monkey patch anything.

Note:: obviously, this mode will not enable all the features offered by bento.
If it were possible, bento would not have been written in the first place.
Nevertheless, the following commands should work relatively well as long as you
don't have hooks:

    * sdist
    * bdist_egg
    * install

This should be enough for pip install foo or easy_install foo to work for a
bento-based package.
