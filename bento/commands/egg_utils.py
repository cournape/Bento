import os
import sys
import zipfile

from six.moves import cStringIO

from bento._config \
    import \
        BUILD_MANIFEST_PATH
from bento.conv \
    import \
        to_distutils_meta
from bento.core \
    import \
        PackageMetadata
from bento.installed_package_description \
    import \
        iter_source_files, BuildManifest

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
    def from_build_manifest(cls, build_manifest, src_node):
        meta = PackageMetadata.from_build_manifest(build_manifest)
        executables = build_manifest.executables

        file_sections = build_manifest.resolve_paths(src_node)
        sources = list([n.abspath() for n in iter_source_files(file_sections)])

        ret = cls(meta, executables, sources)
        ret.build_manifest = build_manifest
        return ret

    def __init__(self, meta, executables, sources):
        self._dist_meta = to_distutils_meta(meta)

        self.sources = sources
        self.meta = meta
        self.executables = executables
        self.build_manifest = None

    def get_pkg_info(self):
        tmp = cStringIO()
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

    def get_build_manifest_info(self, build_manifest_node):
        # FIXME: this is wrong. Rethink the EggInfo interface and its
        # relationship with build_manifest
        if self.build_manifest is None:
            return build_manifest_node.read()
        else:
            tmp = cStringIO()
            self.build_manifest._write(tmp)
            ret = tmp.getvalue()
            tmp.close()
            return ret

    def iter_meta(self, build_node):
        build_manifest_node = build_node.make_node(BUILD_MANIFEST_PATH)
        func_table = {
                "pkg_info": self.get_pkg_info,
                "sources": self.get_sources,
                "install_requires": self.get_install_requires,
                "top_levels": self.get_top_levels,
                "not_zip_safe": self.get_not_zip_safe,
                "dependency_links": self.get_dependency_links,
                "entry_points": self.get_entry_points,
                "build_manifest_info": lambda: self.get_build_manifest_info(build_manifest_node),
            }
        file_table = {
                "pkg_info": "PKG-INFO",
                "sources": "SOURCES.txt",
                "install_requires": "requires.txt",
                "top_levels": "top_level.txt",
                "not_zip_safe": "not-zip-safe",
                "dependency_links": "dependency_links.txt",
                "entry_points": "entry_points.txt",
                "build_manifest_info": "build_manifest.info",
            }

        for k in func_table:
            yield file_table[k], func_table[k]()

def extract_egg(egg, extract_dir):
    # Given a bento-produced egg, extract its content in the given directory,
    # and returned the corresponding build_manifest info instance
    build_manifest = BuildManifest.from_egg(egg)
    # egg scheme
    build_manifest.update_paths({"prefix": ".", "eprefix": ".", "sitedir": "."})

    zid = zipfile.ZipFile(egg)
    try:
        for type, sections in build_manifest.files.items():
            for name, section in sections.items():
                target_dir = build_manifest.resolve_path(section.target_dir)
                section.source_dir = os.path.join(extract_dir, target_dir)
                for source, target in section.files:
                    g = os.path.join(target_dir, target)
                    g = os.path.normpath(g)
                    zid.extract(g, extract_dir)
    finally:
        zid.close()

    return build_manifest
