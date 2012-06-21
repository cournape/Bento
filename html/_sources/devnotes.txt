Build workflow
==============

The main issue blocking bento alpha release is customization of new types of
built "entities". The main constraints:

    - we need to keep a consistent interface at install time
    - we need to register some outputs *before* the files actually exist
      (extensions, generated python code, etc...)
    - the system should be flexible enough so that one can add new types of
      files (ctypes shared library, etc...)

Suggested architecture::

	bento.info -> PackageDescription -> NodePackageDescription -> OutputRegistry -> InstalledSectionRegistry
		                                							    ^
					                        Register in hook   ---------|

Justification for the concepts:

    - bento.info : obvious
    - PackageDescription: python representation of a bento.info
    - NodePackageDescription: is made available in hooks. A node representation
      is much more reliable for recursive and out-of-tree support. Any node in
      a NodePackageDescription *must* be on the fs already.
    - OutputRegistry: this is an adapter to InstdalledSectionRegistry. This is
      needed to provide a common interfance to InstalledSectionRegistry,
      whether entities are built (extension, compiled library, etc...) or
      directly taken from sources (modules, python packages, data files).
      Nodes may or may not exist when defined there
    - InstalledSectionRegistry: at that point, any "entity" is simply a list of
      files + just enough metadata for install. Nodes must exists on the fs.

Current handling:
	
    - build context initialization:
	- PackageDescription -> NodePackageDescription instance (used in pre/post/override hooks)
		- Initialize Output Registry (per category + optionally name)
		- Initialize Builder Registry (per category + optionally name)
		- Initialize Installed Section Registry (per category + optionally name)
    - execite pre_build hooks
    - execute build command run:
       - register data, packages and modules into OutputRegistry
	   - run self.compile (overridable by context subclasses)
			- build executables, and register to OutputRegistry
			- build extensions and compiled libraries, and register
			  to OutputRegistry
			- build additional stuff
    - execute build command post_compiled
        - Convert OutputRegistry objects into InstalledSectionRegistry
	- post_build hooks
	- context.shutdown

	- pre_install hooks
	- install run:
		- load ipkg.info
		- install each installed section with same installer
	- post_install hooks
