Single-file distribution
========================

Ultimately, deployment is about making your code available to your users:
adding a dependency on bento in your package goes against it. To that goal,
bento sources include a script which build a single file distribution of
bento::

    python tools/singledist.py

This creates a bentomaker (bentomaker.exe on windows) file which contains
*everything* needed to configure, build and install software packaged with
bento. You only need to include this file in your source tarball, and that's
it -- no need to install anything.

How does this work ?
--------------------

The process is taken from the waf project, and is basically a simple python
script which contains enough code to bootstrap itself, and a long ascii-encoded
string representing the full bento code compressed in bzip2 format

Note:: as of today, most of the space is taken by windows executables. If you
don't support windows, you can strip down the size to around 120 kb::

    python tools/singledist.py --noinclude-exe
