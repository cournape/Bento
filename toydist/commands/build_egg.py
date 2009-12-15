import os

from toydist.package import \
        PackageDescription
from toydist.conv import \
        to_distutils_meta
from toydist.installed_package_description import \
        InstalledPkgDescription

from toydist.commands.core import \
        Command, SCRIPT_NAME, UsageException

class BuildEggCommand(Command):
    long_descr = """\
Purpose: build egg
Usage:   toymaker build_egg [OPTIONS]"""
    short_descr = "build egg."

    def run(self, opts):
        self.set_option_parser()
        o, a = self.parser.parse_args(opts)
        if o.help:
            self.parser.print_help()
            return

        filename = "installed-pkg-info"
        if not os.path.exists(filename):
            raise UsageException("%s: error: %s subcommand require executed build" \
                    % (SCRIPT_NAME, "build_egg"))

        ipkg = InstalledPkgDescription.from_file(filename)

        import shutil
        basedir = "tmpdist"
        egg_info = os.path.join(basedir, "EGG-INFO")

        if os.path.exists(basedir):
            shutil.rmtree(basedir)
        os.makedirs(basedir)
        os.makedirs(egg_info)

        # Write PKG-INFO
        from toydist.meta import PackageMetadata

        meta = PackageMetadata.from_installed_pkg_description(ipkg)

        dmeta = to_distutils_meta(meta)
        fid = open(os.path.join(egg_info, "PKG-INFO"), "w")
        try:
            dmeta.write_pkg_file(fid)
        finally:
            fid.close()

        # Write SOURCES.txt
        # XXX: bdist_egg includes extra source files here. Should we do the
        # same for compatibility ?
        files = []
        file_sections = ipkg.resolve_paths()
        for name, value in file_sections.items():
            files.extend([f[0] for f in value])
        fid = open(os.path.join(egg_info, "SOURCES.txt"), "w")
        try:
            fid.writelines("\n".join([os.path.normpath(f) for f in files]))
        finally:
            fid.close()

        # Write requires.txt
        fid = open(os.path.join(egg_info, "requires.txt"), "w")
        try:
            fid.write("\n".join(meta.install_requires))
        finally:
            fid.close()

