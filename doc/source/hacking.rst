Design document
===============

.. Version: 0.0.2

Bento is currently split into two parts: a core API to parse the
package description into a simple object API, and a commands API which
gives a command line interface to bento.

The principle philosophy of bento is to clearly separate the
different stages of packaging deployment, as we believe it is the only
way to make a build tool extensible.

Commands "protocol"
-------------------

The command line interface of bento currently supports 3 stages:

        - configuration: is concerned with configuring user options
          (build/install customization).
        - build: compile C extensions
        - install: deploy the software into the system as configured
          at the first stage

In addition, there are a few binary build, which build various
platform-specific binary installers (windows installer-only for now)
and eggs. From an implementation POV, those are similar to the install
stage.

Although those stages are very similar to distutils/setuptools
mechanism, the implementation is fundamentally different, because each
stage is independent from the other. No python object is passed
between commands - the current bentomaker implementation implements each
stage as a separate run:

        - the configuration stage produces a Configuration Context
          object which records every user option (+ some caching
          information) which is dumped into a file.
        - the build stages starts from the dump, and has to produce a
          package manifest (InstalledPkgDescription). The package
          manifst contains the package metadata, installation path
          details as well as file sections.
        - Both installation and binary installers builders stages
          starts from the build manifest.

The package manifest is inspired by the Cabal concept of installed
package info, but has been extended to be independent of the
installation scheme. In particular, for a given build, the same build
manifest can be used to install the package, produces an egg or a
windows installer.
