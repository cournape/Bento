import os
import sys
import string
import zipfile
import tempfile

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from toydist.private.bytecode import \
        compile
from toydist.core.utils import \
        pprint
from toydist.core import \
        PackageMetadata
from toydist.conv import \
        to_distutils_meta
from toydist.installed_package_description import \
        InstalledPkgDescription, iter_files

from toydist.commands.core import \
        Command, SCRIPT_NAME, UsageException
from toydist.commands.build_egg import \
        EggInfo, egg_info_dirname
from toydist.commands.wininst_utils import \
        wininst_filename, create_exe

class BuildWininstCommand(Command):
    long_descr = """\
Purpose: build wininst
Usage:   toymaker build_wininst [OPTIONS]"""
    short_descr = "build wininst."

    def run(self, opts):
        self.set_option_parser()
        o, a = self.parser.parse_args(opts)
        if o.help:
            self.parser.print_help()
            return

        filename = "installed-pkg-info"
        if not os.path.exists(filename):
            raise UsageException("%s: error: %s subcommand require executed build" \
                    % (SCRIPT_NAME, "build_wininst"))

        ipkg = InstalledPkgDescription.from_file(filename)
        meta = PackageMetadata.from_ipkg(ipkg)

        # XXX: do this correctly, maybe use same as distutils ?
        fid, arcname = tempfile.mkstemp(prefix="zip")

        wininst = wininst_filename(os.path.join("toydist", meta.fullname))
        wininst_dir = os.path.dirname(wininst)
        if wininst_dir:
            if not os.path.exists(wininst_dir):
                os.makedirs(wininst_dir)

        egg_info_dir = os.path.join("PURELIB", egg_info_dirname(meta.fullname))
        egg_info = EggInfo.from_ipkg(ipkg)

        zid = zipfile.ZipFile(arcname, "w", zipfile.ZIP_DEFLATED)
        try:
            for filename, cnt in egg_info.iter_meta():
                zid.writestr(os.path.join(egg_info_dir, filename), cnt)

            ipkg.path_variables["prefix"] = "SCRIPTS"
            ipkg.path_variables["sitedir"] = "PURELIB"
            ipkg.path_variables["gendatadir"] = "$sitedir"

            file_sections = ipkg.resolve_paths()
            for kind, source, target in iter_files(file_sections):
                zid.writestr(target, source)

        finally:
            zid.close()
            os.close(fid)

        create_exe(ipkg, arcname, wininst)
