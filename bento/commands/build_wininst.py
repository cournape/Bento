import os
import sys
import string
import zipfile
import tempfile

if sys.version_info[0] < 3:
    from StringIO \
        import \
            StringIO
else:
    from io \
        import \
            StringIO

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
        Command
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

        n = ctx.build_node.make_node(IPKG_PATH)
        ipkg = InstalledPkgDescription.from_file(n.abspath())
        create_wininst(ipkg, src_root_node=ctx.build_node, build_node=ctx.build_node)

def create_wininst(ipkg, src_root_node, build_node, egg_info=None, wininst=None):
    meta = PackageMetadata.from_ipkg(ipkg)
    if egg_info is None:
        egg_info = EggInfo.from_ipkg(ipkg, build_node)

    # XXX: do this correctly, maybe use same as distutils ?
    if wininst is None:
        wininst = wininst_filename(os.path.join("dist", meta.fullname))
    ensure_dir(wininst)

    egg_info_dir = os.path.join("PURELIB", egg_info_dirname(meta.fullname))

    fid, arcname = tempfile.mkstemp(prefix="zip")
    zid = compat.ZipFile(arcname, "w", compat.ZIP_DEFLATED)
    try:
        for filename, cnt in egg_info.iter_meta(build_node):
            zid.writestr(os.path.join(egg_info_dir, filename), cnt)

        wininst_paths = compat.defaultdict(lambda: r"DATA\share\$pkgname")
        wininst_paths.update({"bindir": "SCRIPTS", "sitedir": "PURELIB",
                              "gendatadir": "$sitedir"})
        d = {}
        for k in ipkg._path_variables:
            d[k] = wininst_paths[k]
        ipkg.update_paths(d)
        file_sections = ipkg.resolve_paths(src_root_node)

        def write_content(source, target, kind):
            zid.write(source.abspath(), target.abspath())

        for kind, source, target in iter_files(file_sections):
            write_content(source, target, kind)

    finally:
        zid.close()
        os.close(fid)

    create_exe(ipkg, arcname, wininst)
