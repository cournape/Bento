.. Fri, 13 Nov 2009 17:15:13 +0900

This file documents the different path available through autoconf, and what
they default to on Unix. It include suggestions for their meaning other on
platforms (Mac OS X and Windows).

Installation directories
------------------------

    .# prefix=PREFIX        install architecture-independent files in PREFIX.
                            That's more or less the equivalent of base in
                            distutils install command.
                            Unix default: /usr/local
                            Windows default: C:\ (SYSTEM_ROOT ?)
    .# exec-prefix=EPREFIX  install architecture-dependent files in EPREFIX.
                            Unix default: $prefix
                            Windows default: $prefix
    .# bindir=DIR           user executables.
                            Unix default: $eprefix/bin
                            Windows default: $eprefix/$python_scripts_dir
    .# sbindir=DIR          system admin executables
                            Unix default: $eprefix/sbin
                            Windows default: $eprefix/$python_scripts_dir
    .# libexecdir=DIR       program executables.
                            Unix default: $eprefix/libexec
                            Windows default: $eprefix/$python_scripts_dir
    .# sysconfdir=DIR       read-only single-machine data.
                            Unix default: $prefix/etc
    .# sharedstatedir=DIR   modifiable architecture-independent data.
                            Unix default: $prefix/com
    .# localstatedir=DIR    modifiable single-machine data.
                            Unix default: $prefix/var
    .# libdir=DIR           object code libraries
                            Unix default: $eprefix/lib
    .# includedir=DIR       C header files.
                            Unix default: $prefix/include
    .# oldincludedir=DIR    C header files for non-gcc.
                            Unix default: /usr/include
    .# datarootdir=DIR      read-only arch.-independent data root.
                            Unix default: $prefix/share
    .# datadir=DIR          read-only architecture-independent data.
                            Unix default: $datarootdir
    .# infodir=DIR          info documentation.
                            Unix default: $datarootdir/info
    .# localedir=DIR        locale-dependent data
                            Unix default: $datarootdir/locale
    .# mandir=DIR           man documentation.
                            Unix default: $datarootdir/man
    .# docdir=DIR           documentation root.
                            Unix default: $datarootdir/doc/libsndfile
    .# htmldir=DIR          html documentation.
                            Unix default: $docdir
    .# dvidir=DIR           dvi documentation
                            Unix default: $docdir
    .# pdfdir=DIR           pdf documentation
                            Unix default: $docdir
    .# psdir=DIR            ps documentation
                            Unix default: $docdir

Python directories and variables
--------------------------------

    .# base=BASE
    .# scripts=SCRIPTS      Where to put scripts
    .# platlib/purelib
