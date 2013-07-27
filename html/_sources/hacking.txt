Design notes
============

.. Version: 0.0.3

This is not really readable at the moment, mostly some personal notes about
current internal design.

Bento is currently split into two parts: a core API to parse the
package description into a simple object API, and a commands library
which gives a command line interface to bento.

The main design philosophy of bento is to clearly separate the
different stages of packaging deployment, as we believe it is the only
way to make a build tool extensible.

Commands "protocol"
-------------------

The command line interface of bento currently supports 3 stages:

        - configuration: is concerned with configuring user options
          (build/install customization).
        - build: compile C extensions
        - install: deploy the software into the system as configured
          at the first stage. Installers are considered installation
          as well for reasons explained later.

Although those stages are very similar to distutils/setuptools
mechanism, the implementation is fundamentally different, because each
stage is mostly independent from each other. No python object is
directly shared between commands - the current bentomaker
implementation implements each stage as a separate run. Once
configured, every command has access to all options.

Build manifest and building installers
--------------------------------------

Bento uses a slightly unusal process to install the bits of your package.
Instead of copying directly the files to the desired location, the install
process is driven by a build manifest. This build manifest is produced by the
build command. It contains a description of files per category as well as a few
metadata. The syntax is based of JSON so that it can easily be parsed from any
language and in most environments (local machine, browser, etc...).

Format internals
~~~~~~~~~~~~~~~~

(This is likely to change in the future)

The json file contains 4 elements:

        - meta: this contains the metadata (as defined in the relevant
          packaging PEP)
        - install_paths: a dict of the configured paths
        - file_sections: a list of so-called file sections
        - executables: a list of executable sections

File sections
*************

A list of dictionaries. Each dictionary contains:

        - category: the category name
        - name: name of this section
        - files: a list of tuple source -> target
        - source_dir: os.path.join(source_dir, source) gives an absolute path
          for each source file
        - target_dir: os.path.join(target_dir, target) gives an absolute path
          for each target file

Note that both source_dir and target_dir can refer to path variables as defined
in the install_paths section. This allows to "retarget" a build tree to
different tree configurations, as required by different packages formats.

Example::

       "category": "executables",
            "files": [
                [
                    "bentomaker-2.7",
                    "bentomaker"
                ]
            ],
            "name": "bentomaker",
            "source_dir": "$_srcrootdir/scripts-2.7",
            "target_dir": "$bindir"

This is interpreted as installing the file
$_srcrootdir/scripts-2.7/bentomaker-2.7 into $bindir/bentomaker.

Advantages
~~~~~~~~~~

The built bits and the build manifest are enough to install the
software to arbitrary location, so that the install process does not
need to know anything about the build process.  Conversely, as long as
you can produce a build manifest, you can use the installation
commands as is.

Besides installation, the manifest is also used to produce installers.
Currently, windows installers (both .exe and .msi), eggs and mpkg are
supported, and adding new types of installers should be easier than with
distutils. If you look at the build_wininst and build_egg commands source code,
they are simple, and most of the "magic" happens in the build manifest. In
particular, the build manifest still refers to installed bits relatively to
abstract paths, and those paths are resolved when building the installers.

Installers conversion
~~~~~~~~~~~~~~~~~~~~~

The build manifest is intended to be included in each produced
installer, for convertion between various formats. The goal is to have
idempotent conversions (e.g.  converting an egg to wininst and then
converting it back to an egg produces the exact same egg).

We also intend to use build manifest for the upcoming ''nest''
service, which will contain a database of installed software.
