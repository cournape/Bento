import sys
import os

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from toydist.installed_package_description import \
        iter_source_files
from toydist.conv import \
        to_distutils_meta

from toydist.core import \
        PackageMetadata

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
    def from_ipkg(cls, ipkg):
        meta = PackageMetadata.from_ipkg(ipkg)
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
                "top_levels": "top_level.txt",
                "not_zip_safe": "not-zip-safe",
                "dependency_links": "dependency_links.txt",
                "entry_points": "entry_points.txt",
            }

        for k in func_table:
            yield file_table[k], func_table[k]()
