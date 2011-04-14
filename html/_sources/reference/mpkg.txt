This is a few notes from reverse-engineering the pkg and mpkg format from Apple.

Pkg format
==========

This is a directory. For a simple set of files, this looks as follows::

    Contents/
        Archive.bom
        Archive.pax.gz
        Info.plist
        PkgInfo
        Resources/
            en.lproj/
                Description.plist
            package_version

Description of those files:

    * Archive.bom: bill-of-materials, made through the binary mkbom::

        mkbom source_directory Archive.bom

    * Archive.pax.gz: pax archive of the files, made with pax + cpio::

        pax  -w -f dest -x cpio -z .

    * Info.plist: XML file, supported through plistlib (part of python stdlib since ?)

    * PkgInfo: text file with fixed content::

        pmkrpkg1

