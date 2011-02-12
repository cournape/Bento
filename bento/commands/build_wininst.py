import os
import sys
import string
import zipfile
import tempfile

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from bento.private.bytecode import \
        bcompile
from bento.core.utils import \
        pprint, ensure_dir
from bento._config \
    import \
        IPKG_PATH
from bento.core import \
        PackageMetadata
from bento.conv import \
        to_distutils_meta
from bento.installed_package_description import \
        InstalledPkgDescription, iter_files

from bento.commands.errors \
    import \
        UsageException
from bento.commands.core import \
        Command, SCRIPT_NAME
from bento.commands.egg_utils import \
        EggInfo, egg_info_dirname
from bento.commands.wininst_utils import \
        wininst_filename, create_exe

import bento.compat.api as compat

class BuildWininstCommand(Command):
    long_descr = """\
Purpose: build wininst
Usage:   bentomaker build_wininst [OPTIONS]"""
    short_descr = "build wininst."

    def run(self, ctx):
        argv = ctx.get_command_arguments()
        p = ctx.options_context.parser
        o, a = p.parse_args(argv)
        if o.help:
            p.print_help()
            return

        if not os.path.exists(IPKG_PATH):
            raise UsageException("%s: error: %s subcommand require executed build" \
                    % (SCRIPT_NAME, "build_wininst"))

        ipkg = InstalledPkgDescription.from_file(IPKG_PATH)
        create_wininst(ipkg)

def create_wininst(ipkg, egg_info=None, src_root_dir=".", wininst=None):
    meta = PackageMetadata.from_ipkg(ipkg)
    if egg_info is None:
        egg_info = EggInfo.from_ipkg(ipkg)

    # XXX: do this correctly, maybe use same as distutils ?
    if wininst is None:
        wininst = wininst_filename(os.path.join("dist", meta.fullname))
    ensure_dir(wininst)

    egg_info_dir = os.path.join("PURELIB", egg_info_dirname(meta.fullname))

    fid, arcname = tempfile.mkstemp(prefix="zip")
    zid = compat.ZipFile(arcname, "w", compat.ZIP_DEFLATED)
    try:
        for filename, cnt in egg_info.iter_meta():
            zid.writestr(os.path.join(egg_info_dir, filename), cnt)

        ipkg.update_paths({"bindir": "SCRIPTS", "sitedir": "PURELIB", "gendatadir": "$sitedir"})
        file_sections = ipkg.resolve_paths(src_root_dir)

        def write_content(source, target, kind):
            zid.write(source, target)

        for kind, source, target in iter_files(file_sections):
            write_content(source, target, kind)

    finally:
        zid.close()
        os.close(fid)

    create_exe(ipkg, arcname, wininst)
