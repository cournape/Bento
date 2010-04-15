import os
import zipfile

from toydist.private.bytecode import \
        compile
from toydist.core.utils import \
        pprint
from toydist.core import \
        PackageMetadata
from toydist.installed_package_description import \
        InstalledPkgDescription, iter_files

from toydist.commands.errors \
    import \
        UsageException
from toydist.commands.core import \
        Command, SCRIPT_NAME
from toydist.commands.egg_utils import \
        EggInfo, egg_filename

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
        meta = PackageMetadata.from_ipkg(ipkg)

        egg_info = EggInfo.from_ipkg(ipkg)

        # FIXME: fix egg name
        egg = egg_filename(os.path.join("toydist", meta.fullname))
        egg_dir = os.path.dirname(egg)
        if egg_dir:
            if not os.path.exists(egg_dir):
                os.makedirs(egg_dir)

        egg_info = EggInfo.from_ipkg(ipkg)

        zid = zipfile.ZipFile(egg, "w", zipfile.ZIP_DEFLATED)
        try:
            for filename, cnt in egg_info.iter_meta():
                zid.writestr(os.path.join("EGG-INFO", filename), cnt)

            ipkg.path_variables["sitedir"] = "."
            file_sections = ipkg.resolve_paths()
            for kind, source, target in iter_files(file_sections):
                if not kind in ["executables"]:
                    zid.write(source, target)

            pprint("PINK", "Byte-compiling ...")
            for kind, source, target in iter_files(file_sections):
                if kind in ["pythonfiles"]:
                    zid.writestr("%sc" % target, compile(source))
        finally:
            zid.close()

        return 
