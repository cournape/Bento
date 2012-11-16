import shutil

from bento._config \
    import \
        BUILD_MANIFEST_PATH
from bento.commands.core \
    import \
        Command, Option
from bento.commands.msi_utils \
    import \
        create_msi_installer
from bento.installed_package_description \
    import \
        BuildManifest, iter_files
from bento.private.bytecode \
    import \
        bcompile, PyCompileError

def build_msi_tree(build_manifest, src_root_node, msi_tree_root):
    msi_scheme = {"prefix": msi_tree_root.abspath(),
                  "eprefix": msi_tree_root.abspath()}

    for kind, source, target in build_manifest.iter_built_files(src_root_node, msi_scheme):
        if kind == "pythonfiles":
            compiled = target.change_ext(".pyc")
            compiled.safe_write(bcompile(source.abspath()))
        target.parent.mkdir()
        shutil.copy(source.abspath(), target.abspath())

class BuildMsiCommand(Command):
    long_descr = """\
Purpose: build MSI
Usage:   bentomaker build_msi [OPTIONS]"""
    short_descr = "build msi."
    common_options = Command.common_options \
                        + [Option("--output-dir",
                                  help="Output directory", default="dist"),
                           Option("--output-file",
                                  help="Output filename")]

    def run(self, context):
        o, a = context.get_parsed_arguments()
        if o.help:
            p.print_help()
            return
        output_dir = o.output_dir
        output_file = o.output_file

        n = context.build_node.find_node(BUILD_MANIFEST_PATH)
        manifest = BuildManifest.from_file(n.abspath())
        msi_root = context.build_node.make_node("msi")

        build_msi_tree(manifest, context.build_node, msi_root)

        create_msi_installer(context.pkg, context.run_node, msi_root, o.output_file, o.output_dir)
