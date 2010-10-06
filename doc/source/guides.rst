======
Guides
======

Metadata
========

Bento supports most metadata defined in the PEP 241 and 314::

    Name: foo
    Version: 0.0.1
    Summary: a few words
    Description: you can
        use multiple lines here
    Url: http://example.com
    DownloadUrl: http://example.com
    Author: John Doe
    AuthorEmail: john@doe.com
    Maintainer: John Doe
    MaintainerEmail: john@doe.com
    License: BSD
    Platforms: darwin, win32
    InstallRequires: foo
    BuildRequires: bar

Customizable installation paths
===============================

Most packages have some files besides pure code: configuration, data
files, documentation, etc... When those files need to be installed,
you should use DataFiles sections. Each such section has two mandatory
fields, to specify the target directory (where files are installed)
and which files are specific to this section::

    DataFiles: manage
        TargetDir: /usr/man/man1
        Files: fubar/fubar1

This will install the file top_dir/fubar/fubar1 into
/usr/man/man1/fubar/fubar1.

Flexible install scheme
~~~~~~~~~~~~~~~~~~~~~~~

Hardcoding the target directory as above is not flexibe. The user may
want to install manpages somewhere else. Bento defines a set of
variable paths which are customizable, with platform-specific
defaults. For manpages, the variable is mandir::

    DataFiles: manpage
        TargetDir: $mandir/man1
        Files: fubar/fubar.1

Now, the installation path is customizable, e.g.::

    bentomaker configure --mandir=/opt/man

will cause the target directory to translate to /opt/man/man1.
Moreover, as mandir default value is $prefix/man, modifying the prefix
will also change how mandir is expanded at install time::

    # $mandir is automatically expanded to /opt/man
    bentomaker configure --prefix=/opt

If you do not want to install files with their directory component,
you need to use the SourceDir option::

    DataFiles: manpage
        TargetDir: $mandir
        SourceDir: fubar
        Files: fubar.1

will install fubar/fubar.1 as $mandir/fubar.1 instead of
$mandir/fubar/fubar.1.

Custom data paths
-----------------

TODO

Retrieving data files at runtime
================================

It is often necessary to retrieve data files from your python code. The
simplest way to do so is to use __file__ and refer to data files relatively to
python code. This is not very flexible, because it requires to deal with
platform idiosyncraties w.r.t. files location.  Setuptools and its descendents
has an alternative mechanism to retrieve resources at runtime, implemented in
the pkg_resource module.

Bento uses a much simpler system, based on a simple python module generated at
install time, containing all the relevant information. This is an opt-in
feature::

    ConfigPy: foo/__bento_config.py

This tells bento to generate a module, and install it into
foo/__bento_config.py. The path is always relative to site-packages.
The file looks as follows::

    DOCDIR = "/usr/local/share/doc/config_py"
    SHAREDSTATEDIR = "/usr/local/com"
    ...

So you can import every path variable with their expanded value in
your package::

    try:
        from foo.__bento_config import DOCDIR, SHAREDSTATEDIR
    except ImportError:
        # Default values (so that the package may be imported/used without
        # being built)
        DOCDIR = ...

Recursive package description
=============================

Hook files
==========

Conditional packaging
=====================

Adding new commands
===================
