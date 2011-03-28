import os
import sys
import tempfile
import shutil

from bento.core.platforms.sysconfig \
    import \
        get_scheme
from bento.core.utils \
    import \
        subst_vars
from bento.installed_package_description \
    import \
        InstalledPkgDescription, iter_files
from bento._config \
    import \
        IPKG_PATH
from bento.commands.core \
    import \
        Command, SCRIPT_NAME
from bento.commands.mpkg_utils \
    import \
        build_pkg, PackageInfo, MetaPackageInfo, make_mpkg_plist, make_mpkg_description

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

    def run(self, ctx):
        argv = ctx.get_command_arguments()
        p = ctx.options_context.parser
        o, a = p.parse_args(argv)
        if o.help:
            p.print_help()
            return

        if not os.path.exists(IPKG_PATH):
            raise UsageException("%s: error: %s subcommand require executed build" \
                    % (SCRIPT_NAME, "build_mpkg"))

        root = ctx.top_node
        while root.height() > 0:
            root = root.parent

        default_scheme = get_default_scheme(ctx.pkg.name)
        default_prefix = default_scheme["prefix"]
        default_sitedir = default_scheme["sitedir"]

        ipkg = InstalledPkgDescription.from_file(IPKG_PATH)

        categories = set()
        file_sections = ipkg.resolve_paths(".")
        for kind, source, target in iter_files(file_sections):
            categories.add(kind)

        # Mpkg metadata
        mpkg_root = os.path.join(os.getcwd(), "dist", "bento.mpkg")
        mpkg_cdir = os.path.join(mpkg_root, "Contents")
        if os.path.exists(mpkg_root):
            shutil.rmtree(mpkg_root)
        os.makedirs(mpkg_cdir)
        f = open(os.path.join(mpkg_cdir, "PkgInfo"), "w")
        try:
            f.write("pmkrpkg1")
        finally:
            f.close()
        mpkg_info = MetaPackageInfo.from_ipkg(ipkg)
        mpkg_info.packages = ["bento-purelib.pkg", "bento-scripts.pkg", "bento-datafiles.pkg"]
        make_mpkg_plist(mpkg_info, os.path.join(mpkg_cdir, "Info.plist"))

        mpkg_rdir = os.path.join(mpkg_root, "Contents", "Resources")
        os.makedirs(mpkg_rdir)
        make_mpkg_description(mpkg_info, os.path.join(mpkg_rdir, "Description.plist"))

        # Package the stuff which ends up into site-packages
        pkg_root = os.path.join(mpkg_root, "Contents", "Packages", "bento-purelib.pkg")
        build_pkg_from_temp(ipkg, pkg_root, root, "/", ["pythonfiles"])

        pkg_root = os.path.join(mpkg_root, "Contents", "Packages", "bento-scripts.pkg")
        build_pkg_from_temp(ipkg, pkg_root, root, "/", ["executables"])

        pkg_root = os.path.join(mpkg_root, "Contents", "Packages", "bento-datafiles.pkg")
        build_pkg_from_temp(ipkg, pkg_root, root, "/", ["bentofiles", "datafiles"])

def build_pkg_from_temp(ipkg, pkg_root, root_node, install_root, categories):
    d = tempfile.mkdtemp()
    try:
        tmp_root = root_node.make_node(d)
        prefix_node = tmp_root.make_node(root_node.make_node(sys.exec_prefix).path_from(root_node))
        prefix = eprefix = prefix_node.abspath()
        ipkg.update_paths({"prefix": prefix, "eprefix": eprefix})
        file_sections = ipkg.resolve_paths(".")
        for kind, source, target in iter_files(file_sections):
            if kind in categories:
                if not os.path.exists(os.path.dirname(target)):
                    os.makedirs(os.path.dirname(target))
                shutil.copy(source, target)

        pkg_info = PackageInfo(pkg_name=ipkg.meta["name"],
            prefix=install_root, source_root=d, pkg_root=pkg_root)
        build_pkg(pkg_info)
    finally:
        shutil.rmtree(d)
