========================================================
Transition from existing python packaging infrastructure
========================================================

Converting distutils-based packages
===================================

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

    from setuptools import setup

    if __name__ == '__main__':
        setup()

will enable commands such as::

    python setup.py install
    python setup.py sdist

to work as expected, taking all the package information from bento.info file.

Note:: obviously, this mode will not enable all the features offered by bento.
If it were possible, bento would not have been written in the first place.
Nevertheless, the following commands should work relatively well as long as you
don't have hooks:

    * sdist
    * bdist_egg
    * install

This should be enough for pip install foo or easy_install foo to work for a
bento-based package.
