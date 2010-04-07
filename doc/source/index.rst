.. Toydist documentation master file, created by
   sphinx-quickstart on Sun Jan  3 12:53:13 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

################################################################
Toydist: an no-nonsense packaging tool for python
################################################################

Toydist is a Python-based packaging solution intended to replace
distutils/setuptools. Packaging simple python code is as simple as
writing the following toysetup.info file::

    Name: Foo
    Author: John Doe

    Library:
        Packages: foo

Toydist contains a command line tools to build and install toydist
packages::

    toymaker configure
    toymaker build
    toymaker install

Toydist aims at being simpler, more pythonic and more extensible than
existing tools. It is currenly in very early stage, and is not
recommended for any production use. Discussions on toydist design
happens on the NumPy Mailing List.

.. toctree::
   :maxdepth: 2

   overview
   features
   reference
   faq
   TODO
   contribute

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
