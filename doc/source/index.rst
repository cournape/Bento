.. Bento documentation master file, created by
   sphinx-quickstart on Sun Jan  3 12:53:13 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

################################################################
Bento: an no-nonsense packaging tool for python
################################################################

Bento is a Python-based packaging solution intended to replace
distutils/setuptools. Packaging simple python code is as simple as
writing the following bento.info file::

    Name: Foo
    Author: John Doe

    Library:
        Packages: foo

Bento contains a command line tools to build and install bento
packages::

    bentomaker configure
    bentomaker build
    bentomaker install

Bento aims at being simpler, more pythonic and more extensible than
existing tools. It is currenly in very early stage, and is not
recommended for any production use. Discussions on bento design
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
