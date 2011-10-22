import sys
import os
import zipfile

if sys.version_info[0] < 3:
    from StringIO \
        import \
            StringIO
else:
    from io \
        import \
            StringIO

from bento.installed_package_description import \
        iter_source_files, InstalledPkgDescription
from bento.conv import \
        to_distutils_meta

from bento.core import \
        PackageMetadata
from bento._config \
    import \
        IPKG_PATH

def egg_filename(fullname, pyver=None):
    if not pyver:
        pyver = ".".join([str(i) for i in sys.version_info[:2]])
    return "%s-py%s.egg" % (fullname, pyver)

def egg_info_dirname(fullname, pyver=None):
    if not pyver:
        pyver = ".".join([str(i) for i in sys.version_info[:2]])
    return "%s-py%s.egg-info" % (fullname, pyver)

class EggInfo(object):
    @classmethod
    def from_ipkg(cls, ipkg, src_node):
        meta = PackageMetadata.from_ipkg(ipkg)
        executables = ipkg.executables

        file_sections = ipkg.resolve_paths(src_node)
        sources = list([n.abspath() for n in iter_source_files(file_sections)])

        ret = cls(meta, executables, sources)
        ret.ipkg = ipkg
        return ret

    def __init__(self, meta, executables, sources):
        self._dist_meta = to_distutils_meta(meta)

        self.sources = sources
        self.meta = meta
        self.executables = executables
        self.ipkg = None

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
        # Last newline added for compatibility with setuptools
        return "\n".join(self.meta.top_levels + [''])

    def get_not_zip_safe(self):
        return "\n"

    def get_dependency_links(self):
        return "\n"

    def get_entry_points(self):
        ret = []
        ret.append("[console_scripts]")
        ret.extend([exe.full_representation() for exe in \
                        self.executables.values()])
        ret.append('')
        return "\n".join(ret)

    def get_ipkg_info(self, ipkg_node):
        # FIXME: this is wrong. Rethink the EggInfo interface and its
        # relationship with ipkg
        if self.ipkg is None:
            return ipkg_node.read()
        else:
            tmp = StringIO()
            self.ipkg._write(tmp)
            ret = tmp.getvalue()
            tmp.close()
            return ret

    def iter_meta(self, build_node):
        ipkg_node = build_node.make_node(IPKG_PATH)
        func_table = {
                "pkg_info": self.get_pkg_info,
                "sources": self.get_sources,
                "install_requires": self.get_install_requires,
                "top_levels": self.get_top_levels,
                "not_zip_safe": self.get_not_zip_safe,
                "dependency_links": self.get_dependency_links,
                "entry_points": self.get_entry_points,
                "ipkg_info": lambda: self.get_ipkg_info(ipkg_node),
            }
        file_table = {
                "pkg_info": "PKG-INFO",
                "sources": "SOURCES.txt",
                "install_requires": "requires.txt",
                "top_levels": "top_level.txt",
                "not_zip_safe": "not-zip-safe",
                "dependency_links": "dependency_links.txt",
                "entry_points": "entry_points.txt",
                "ipkg_info": "ipkg.info",
            }

        for k in func_table:
            yield file_table[k], func_table[k]()

def extract_egg(egg, extract_dir):
    # Given a bento-produced egg, extract its content in the given directory,
    # and returned the corresponding ipkg info instance
    ipkg = InstalledPkgDescription.from_egg(egg)
    # egg scheme
    ipkg.update_paths({"prefix": ".", "eprefix": ".", "sitedir": "."})

    zid = zipfile.ZipFile(egg)
    try:
        for type, sections in ipkg.files.items():
            for name, section in sections.items():
                target_dir = ipkg.resolve_path(section.target_dir)
                section.source_dir = os.path.join(extract_dir, target_dir)
                for source, target in section.files:
                    g = os.path.join(target_dir, target)
                    g = os.path.normpath(g)
                    zid.extract(g, extract_dir)
    finally:
        zid.close()

    return ipkg
