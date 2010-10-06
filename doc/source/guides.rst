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

.. If you have a complex package with a lot of python subpackages, which require
.. custom configuration, doing everything in

Hook files
==========

*Note: the hook API is still in flux, and should not be relied on. It is
documented to give an idea of where bento is going, but I still reserve myself
the right to change things in fundamental ways.*

Although many typical python softwares can be entirely described in bento.info,
complex packages may require a more advanced configuration, e.g.:

    * Conditionally define libraries depending on systems configuration
      (addition features if you have the C library libfoo, etc...)
    * Define new bento commands
    * Customization of the build process (e.g. compiler flags, linked
      libraries, etc...)
    * Adding new tools in the build process (cython, source code generator,
      etc...)
    * Using a different build tool than the one included in bento (waf, scons
      or even make).
    * addition new options to an existing command

Instead of craming too many features in the bento.info, bento allows you to add
one (or more) "hook" files, which are regular python modules, but under the
control of bento.

Simple example: hello world
---------------------------

The hello world for bento hook system is simple: it prints "yummy bento"
everytime you execute bentomaker. Assuming the following bento.info file::

    Name: foo
    HookFile: bscript

the hook file will look like::

    def startup():
        print "Yummy bento"

As its name suggests, the startup method is executed before running any
command, and before bentomaker itself parse the command line. As such, you do
not want to do to many things there -- typically register new commands.

Command hook and bento context
------------------------------

Each command (configure, build, install, etc...) in bento has a
pre_command_name hook, a post_command_hook, and an override hook. Just defining
hooks is not very useful, though - you need to be able to interact with bento
to do interesting things.

Each hook is a regular python function - its hook "status" is defined by the hook decorator(s)::

    from bento.commands.hooks import post_configure

    @post_configure
    def pconfigure(ctx):
        pass

The function takes one parameter, ctx. Its class does not matter much
at this point, but its members do. First, both the command instance
(cmd) and the command options (cmd_opts) are always available. The
command instance corresponds to the requested command (bentomaker
configure -> bento.commands.configure.Configure class). cmd_opts is a simple list of the command line arguments::

    from bento.commands.hooks import post_configure

    @post_configure
    def pconfigure(ctx):
        print ctx.cmd_opts

Each ctx variable also have a pkg member, which is a
PackageDescription instance, and contains most package information.
Metadata, extensions, path options, executables are all available,
which enable the following:

    * access package information to generate new "targets" (new types
      of binary installers)
    * add extra source files whose location cannot be known at
      configure time
    * add/remove/modify extensions, packages dynamically

*Note: unfortunately, there is still no public API for safe
PackageDescription instances access. Most read access should be safe,
but modifying package description members likely to break in the
future*

Conditional packaging
=====================

Adding new commands
===================
