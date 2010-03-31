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
        InstalledPkgDescription

from toydist.commands.core import \
        Command, SCRIPT_NAME, UsageException
#from toydist.commands.build_egg import \
#        write_egg_info, egg_info_dirname
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
        meta = PackageMetadata.from_installed_pkg_description(ipkg)

        # XXX: do this correctly, maybe use same as distutils ?
        fid, arcname = tempfile.mkstemp(prefix="zip")

        wininst = wininst_filename(os.path.join("toydist", meta.fullname))
        wininst_dir = os.path.dirname(wininst)
        if wininst_dir:
            if not os.path.exists(wininst_dir):
                os.makedirs(wininst_dir)

        egg_info = os.path.join("PURELIB", egg_info_dirname(meta.fullname))

        compression = zipfile.ZIP_DEFLATED
        zid = zipfile.ZipFile(arcname, "w", compression=compression)
        try:
            ret = write_egg_info(ipkg)
            try:
                for k, v in ret.items():
                    v.seek(0)
                    zid.writestr(os.path.join(egg_info, k), v.getvalue())
            finally:
                for v in ret.values():
                    v.close()

            # FIXME: abstract file_sections, it is too low-level ATM, and not
            # very practical to use. In Most installers, what is needed is:
            #  - specify a different install scheme per sectio
            # - ?
            ipkg.path_variables["sitedir"] = "."
            ipkg.path_variables["gendatadir"] = "$sitedir"

            file_sections = ipkg.resolve_paths()
            for type in file_sections:
                if type == "executables":
                    basename = "SCRIPTS"
                    for value in file_sections["executables"].values():
                        for f in value:
                            zid.write(f[0], os.path.join(basename, os.path.basename(f[1])))
                elif type in ["pythonfiles", "datafiles"]:
                    # FIXME: how to deal with data files ? Shall we really
                    # install all of them in sphinx ?
                    basename = "PURELIB"
                    for value in file_sections[type].values():
                        for f in value:
                            zid.write(f[0], os.path.join(basename, f[1]))
                else:
                    for value in file_sections[type].values():
                        for f in value:
                            zid.write(f[0], f[1])

            create_exe(ipkg, arcname, wininst)
        finally:
            zid.close()
            os.close(fid)
            os.remove(arcname)

        return 
