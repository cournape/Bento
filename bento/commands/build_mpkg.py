import os
import sys
import tempfile
import shutil

from bento.core.platforms.sysconfig \
    import \
        get_scheme
from bento.utils.utils \
    import \
        subst_vars
from bento.installed_package_description \
    import \
        BuildManifest, iter_files
from bento._config \
    import \
        BUILD_MANIFEST_PATH
from bento.commands.core \
    import \
        Command, Option
from bento.commands.mpkg_utils \
    import \
        build_pkg, PackageInfo, MetaPackageInfo, make_mpkg_plist, make_mpkg_description
from bento.utils.utils \
    import \
        MODE_755

def get_default_scheme(pkg_name, py_version_short=None, prefix=None):
    if py_version_short is None:
        py_version_short = ".".join([str(i) for i in sys.version_info[:2]])
    if prefix is None:
        prefix = sys.exec_prefix
    scheme, _ = get_scheme(sys.platform)
    scheme["prefix"] = scheme["eprefix"] = prefix
    scheme["pkgname"] = pkg_name
    scheme["py_version_short"] = py_version_short
    ret = {}
    for k in scheme:
        ret[k] = subst_vars(scheme[k], scheme)
    return ret

class BuildMpkgCommand(Command):
    long_descr = """\
Purpose: build Mac OS X mpkg
Usage:   bentomaker build_mpkg [OPTIONS]"""
    short_descr = "build mpkg."
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

        root = ctx.top_node
        while root.height() > 0:
            root = root.parent

        default_scheme = get_default_scheme(ctx.pkg.name)
        default_prefix = default_scheme["prefix"]
        default_sitedir = default_scheme["sitedir"]

        n = ctx.build_node.make_node(BUILD_MANIFEST_PATH)
        build_manifest = BuildManifest.from_file(n.abspath())
        name = build_manifest.meta["name"]
        version = build_manifest.meta["version"]
        py_short = ".".join([str(i) for i in sys.version_info[:2]])
        if o.output_file is None:
            mpkg_name = "%s-%s-py%s.mpkg" % (name, version, py_short)
        else:
            mpkg_name = o.output_file

        categories = set()
        file_sections = build_manifest.resolve_paths(ctx.build_node)
        for kind, source, target in iter_files(file_sections):
            categories.add(kind)

        # Mpkg metadata
        mpkg_root = os.path.join(os.getcwd(), o.output_dir, mpkg_name)
        mpkg_cdir = os.path.join(mpkg_root, "Contents")
        if os.path.exists(mpkg_root):
            shutil.rmtree(mpkg_root)
        os.makedirs(mpkg_cdir)
        f = open(os.path.join(mpkg_cdir, "PkgInfo"), "w")
        try:
            f.write("pmkrpkg1")
        finally:
            f.close()
        mpkg_info = MetaPackageInfo.from_build_manifest(build_manifest)

        purelib_pkg = "%s-purelib-%s-py%s.pkg" % (name, version, py_short)
        scripts_pkg = "%s-scripts-%s-py%s.pkg" % (name, version, py_short)
        datafiles_pkg = "%s-datafiles-%s-py%s.pkg" % (name, version, py_short)
        mpkg_info.packages = [purelib_pkg, scripts_pkg, datafiles_pkg]
        make_mpkg_plist(mpkg_info, os.path.join(mpkg_cdir, "Info.plist"))

        mpkg_rdir = os.path.join(mpkg_root, "Contents", "Resources")
        os.makedirs(mpkg_rdir)
        make_mpkg_description(mpkg_info, os.path.join(mpkg_rdir, "Description.plist"))

        # Package the stuff which ends up into site-packages
        pkg_root = os.path.join(mpkg_root, "Contents", "Packages", purelib_pkg)
        build_pkg_from_temp(ctx, build_manifest, pkg_root, root, "/", ["pythonfiles"], "Pure Python modules and packages")

        pkg_root = os.path.join(mpkg_root, "Contents", "Packages", scripts_pkg)
        build_pkg_from_temp(ctx, build_manifest, pkg_root, root, "/", ["executables"], "Scripts and binaries")

        pkg_root = os.path.join(mpkg_root, "Contents", "Packages", datafiles_pkg)
        build_pkg_from_temp(ctx, build_manifest, pkg_root, root, "/", ["bentofiles", "datafiles"], "Data files")

def build_pkg_from_temp(ctx, build_manifest, pkg_root, root_node, install_root, categories, description=None):
    d = tempfile.mkdtemp()
    try:
        tmp_root = root_node.make_node(d)
        prefix_node = tmp_root.make_node(root_node.make_node(sys.exec_prefix).path_from(root_node))
        prefix = eprefix = prefix_node.abspath()
        build_manifest.update_paths({"prefix": prefix, "eprefix": eprefix})
        file_sections = build_manifest.resolve_paths(ctx.build_node)
        for kind, source, target in iter_files(file_sections):
            if kind in categories:
                #if not os.path.exists(target.parent.abspath()):
                #    os.makedirs(os.path.dirname(target))
                target.parent.mkdir()
                shutil.copy(source.abspath(), target.abspath())
                if kind == "executables":
                    os.chmod(target.abspath(), MODE_755)

        pkg_name = os.path.splitext(os.path.basename(pkg_root))[0]
        pkg_info = PackageInfo(pkg_name=pkg_name,
            prefix=install_root, source_root=d, pkg_root=pkg_root, description=description)
        build_pkg(pkg_info)
    finally:
        shutil.rmtree(d)
