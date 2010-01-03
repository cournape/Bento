Ideas and syntax about the static file format

Field form
==========

Each field is of the form field:value (RFC 822-like format)::

        #. Field is not case-sensitive
        #. Values are case-sensitive
        #. Line continuation of a value is done by one indentation, relatively
        to the field

Syntax for values
-----------------

Several possibilities::

        #. token, filename, directory: sequence of characters without space, or
        quoted string (format for quoted string ?)
        #. freeform, url, address: arbitrary, uninterpreted string
        #. identifier: letter follows by alphanumerical characters
        #. boolean: True/False

All values are unique (one field only pre section), unless indicated. Non unique values are interpreted as appended values to existing list, e.g.:

        Package: foo
        Package: bar

Is the same as :

        Package: foo, bar

Basic structure
===============

Metadata header
---------------

Mandatory. The file starts with a header, which contains so-called metadata:
this mostly contains the things you would find in the PKG-INFO file. Those
properties apply to the whole "distribution" (package).

        * Name: package-name
        * Version: number
        * Description: freeform
        * ...

Flags declaration
-----------------

Optional. For configuration and customization. Example:

        Flag FlagName
                Description: freeform
                Default: boolean

Library section
---------------

Optional.

All for following examples are equivalent:

        Library:
                Packages: foo.bar, foo.bar

        Library:
                Packages:
                        foo.bar,
                        foo.bar

        Library:
                Packages: foo.bar,
                        foo.bar

        Library:
                Packages: foo.bar
                Packages: foo.bar

Fields::

        #. Packages: list of packages
        #. Modules: list of modules
        #. Extension: one extension

Extension
~~~~~~~~~

Question:

        Extension: extension_name
                Sources: foo.c

Or:

        Extension extension_name
                Sources: foo.c

??

Fields::

        #. Sources: list of files
        #.

Script sections
---------------

Optional

Full example
============

A complete example:

::

        Name: numpy
        Version: 1.3.0
        Description:
            NumPy is a general-purpose array-processing package designed to
            efficiently manipulate large multi-dimensional arrays of arbitrary
            records without sacrificing too much speed for small multi-dimensional
            arrays.  NumPy is built on the Numeric code base and adds features
            introduced by numarray as well as an extended C-API and the ability to
            create arrays of arbitrary type which also makes NumPy suitable for
            interfacing with general-purpose data-base applications.

            There are also basic facilities for discrete fourier transform,
            basic linear algebra and random number generation.
        Summary: array processing for numbers, strings, records, and objects.
        Author: someone
        AuthorEmail: someone@example.com
        Maintainer: someonelse
        MaintainerEmail: someonelse@example.com

        Library:
            Extension: _foo.bar
                if !os(windows)
                    build-depends: m
                sources:
                    foobar.c
                include_dir:
                    /usr/local/include
            Extension: _foo.bar2
                sources:
                    yo2
            Packages:
                foo.bar,
                foo.bar2,
                foo.bar3
            Modules:
                bar,
                foobar

            if os(macosx)
                Extension: backends._macosx
                    sources: macosx.c
            if os(linux)
                Extension: backends._linux
                    sources: linux.c
            if os(windows):
                Extension: backends._linux
                    sources: linux.c

TODO
====

Things which are needed, not implemented::

        .# A true BNF grammar: how to validate ?
        .# Unicode handling ?
        .# Python 3 support ?
