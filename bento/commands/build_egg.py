import os
import warnings

from bento._config \
    import \
        IPKG_PATH
from bento.commands.core \
    import \
        Command, Option
from bento.commands.egg_utils \
    import \
        EggInfo, egg_filename
from bento.core.utils \
    import \
        pprint, ensure_dir, extract_exception
from bento.core \
    import \
        PackageMetadata
from bento.private.bytecode \
    import \
        bcompile, PyCompileError
from bento.installed_package_description \
    import \
        InstalledPkgDescription, iter_files

import bento.compat.api as compat

class BuildEggCommand(Command):
    long_descr = """\
Purpose: build egg
Usage:   bentomaker build_egg [OPTIONS]"""
    short_descr = "build egg."
    common_options = Command.common_options \
                        + [Option("--output-dir",
                                  help="Output directory", default="dist"),
                           Option("--output-file",
                                  help="Output filename")]

    def run(self, ctx):
        argv = ctx.command_argv
        p = ctx.options_context.parser
        o, a = p.parse_args(argv)
        if o.help:
            p.print_help()
            return
        output_dir = o.output_dir
        output_file = o.output_file

        n = ctx.build_node.make_node(IPKG_PATH)
        ipkg = InstalledPkgDescription.from_file(n.abspath())
        build_egg(ipkg, ctx, ctx.build_node, output_dir, output_file)

def build_egg(ipkg, ctx, source_root, output_dir=None, output_file=None):
    meta = PackageMetadata.from_ipkg(ipkg)
    egg_info = EggInfo.from_ipkg(ipkg, ctx.build_node)

    # FIXME: fix egg name
    if output_dir is None:
        if output_file is None:
            egg = egg_filename(os.path.join("dist", meta.fullname))
        else:
            egg = os.path.join("dist", output_file)
    else:
        if output_file is None:
            egg = egg_filename(os.path.join(output_dir, meta.fullname))
        else:
            egg = os.path.join(output_dir, output_file)
    ensure_dir(egg)

    zid = compat.ZipFile(egg, "w", compat.ZIP_DEFLATED)
    try:
        ipkg.update_paths({"prefix": source_root.abspath(),
                           "eprefix": source_root.abspath(),
                           "sitedir": source_root.abspath()})
        for filename, cnt in egg_info.iter_meta(ctx.build_node):
            zid.writestr(os.path.join("EGG-INFO", filename), cnt)

        file_sections = ipkg.resolve_paths(source_root)
        for kind, source, target in iter_files(file_sections):
            if not kind in ["executables"]:
                zid.write(source.abspath(), target.path_from(source_root))

        pprint("PINK", "Byte-compiling ...")
        for kind, source, target in iter_files(file_sections):
            if kind in ["pythonfiles"]:
                try:
                    bytecode = bcompile(source.abspath())
                except PyCompileError:
                    e = extract_exception()
                    warnings.warn("Error byte-compiling %r" % source.abspath())
                else:
                    zid.writestr("%sc" % target.path_from(source_root), bcompile(source.abspath()))
    finally:
        zid.close()

    return
