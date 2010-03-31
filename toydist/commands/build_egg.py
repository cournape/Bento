import os
import sys
import zipfile

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
        InstalledPkgDescription, iter_source_files, iter_files

from toydist.commands.core import \
        Command, SCRIPT_NAME, UsageException

def egg_filename(fullname, pyver=None):
    if not pyver:
        pyver = ".".join([str(i) for i in sys.version_info[:2]])
    return "%s-py%s.egg" % (fullname, pyver)

def egg_info_dirname(fullname, pyver=None):
    if not pyver:
        pyver = ".".join([str(i) for i in sys.version_info[:2]])
    return "%s-py%s.egg-info" % (fullname, pyver)

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
        meta = PackageMetadata.from_installed_pkg_description(ipkg)

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

class EggInfo(object):
    @classmethod
    def from_ipkg(cls, ipkg):
        meta = PackageMetadata.from_installed_pkg_description(ipkg)
        executables = ipkg.executables

        file_sections = ipkg.resolve_paths()
        sources = list(iter_source_files(file_sections))

        return cls(meta, executables, sources)

    def __init__(self, meta, executables, sources):
        self._dist_meta = to_distutils_meta(meta)

        self.sources = sources
        self.meta = meta
        self.executables = executables

    def get_pkg_info(self):
        tmp = StringIO()
        self._dist_meta.write_pkg_file(tmp)
        ret = tmp.getvalue()
        tmp.close()
        return ret

    def get_sources(self):
        return "\n".join([os.path.normpath(f) for f in self.sources])

    def get_install_requires(self):
        return "\n".join(self.meta.install_requires)

    def get_top_levels(self):
        return "\n".join(self.meta.top_levels)

    def get_not_zip_safe(self):
        return "\n"

    def get_dependency_links(self):
        return "\n"

    def get_entry_points(self):
        ret = []
        ret.append("[console_scripts]")
        ret.extend([exe.full_representation() for exe in \
                        self.executables.values()])
        return "\n".join(ret)

    def iter_meta(self):
        func_table = {
                "pkg_info": self.get_pkg_info,
                "sources": self.get_sources,
                "install_requires": self.get_install_requires,
                "top_levels": self.get_top_levels,
                "not_zip_safe": self.get_not_zip_safe,
                "dependency_links": self.get_dependency_links,
                "entry_points": self.get_entry_points,
            }
        file_table = {
                "pkg_info": "PKG-INFO",
                "sources": "SOURCES.txt",
                "install_requires": "requires.txt",
                "top_levels": "top_levels.txt",
                "not_zip_safe": "not-zip-safe.txt",
                "dependency_links": "dependency_links.txt",
                "entry_points": "entry_points.txt",
            }

        for k in func_table:
            yield file_table[k], func_table[k]()
