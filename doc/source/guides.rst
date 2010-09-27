======
Guides
======

Metadata
========

Customizable installation paths
===============================

Path variables, SourceDir, etc...

.. Flexible install scheme
.. ~~~~~~~~~~~~~~~~~~~~~~~
.. 
.. Hardcoding the target directory as above is not flexibe. The user may
.. want to install the package somewhere else. Bento defines a set of
.. variable paths which are customizable, with platform-specific
.. defaults. For manpages, the variable is mandir::
.. 
..     DataFiles: manpage
..         TargetDir: $mandir/man1
..         Files: fubar/fubar.1
.. 
.. Now, the installation path is customizable, e.g.::
.. 
..     bentomaker configure --mandir=/opt/man
.. 
.. will cause the target directory to translate to /opt/man/man1.
.. 
.. If you do not want to install files with their directory component,
.. you need to use the SourceDir option:: 
.. 
..     DataFiles: manpage
..         TargetDir: $mandir
..         SourceDir: fubar
..         Files: fubar.1
.. 
.. will install fubar/fubar.1 as $mandir/fubar.1.
.. 
.. Besides standard paths options, You can define your own new path
.. variables (TODO: path variable section).
.. 

Recursive package description
=============================

Hook files
==========

Retrieving data files at runtime
================================

Conditional packaging
=====================

Adding new commands
===================
