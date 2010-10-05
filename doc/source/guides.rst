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

Recursive package description
=============================

Hook files
==========

Conditional packaging
=====================

Adding new commands
===================
