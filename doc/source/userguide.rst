User guide
==========

Creating a simple package
-------------------------

Almost every metadata supported in distutils/setuptools is supported in toydist
file format. For a simple package containing one module hello, the
toysetup.info would look like::

    Name: hello
    Version: 0.0.1
    Summary: A one-line description of the distribution
    Description:
        A longer, potentially multi-line string.

        As long as the indentation is maintained, the field is considered as
        continued.
    Author: John Doe
    AuthorEmail: john@doe.org
    License: BSD

    Library:
        Packages:
            hello

TODO: specify every metadata field.

Packages containing C extensions
--------------------------------

Packages with data files
------------------------

Installed data vs extra source files.

Adding custom path options
--------------------------

Conditionals
------------

Adding custom flags
-------------------

.. _sphinx: http://sphinx.pocoo.org
