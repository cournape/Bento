import sys

from bento._config \
    import \
        IPKG_PATH
from bento.core.platforms \
    import \
        get_scheme

from distutils.command.build \
    import \
        build as old_build
from bento.commands.build \
    import \
        SectionWriter, _build_config_py

class build(old_build):
    def __init__(self, *a, **kw):
        old_build.__init__(self, *a, **kw)

    def initialize_options(self):
        old_build.initialize_options(self)

    def finalize_options(self):
        old_build.finalize_options(self)

    def _get_install_scheme(self, pkg):
        install = self.get_finalized_command("install")

        # FIXME: this should be centralized with other scheme-related stuff
        scheme = get_scheme(sys.platform)[0]
        scheme["pkgname"] = pkg.name
        py_version = sys.version.split()[0]
        scheme["py_version_short"] = py_version[:3]
        if hasattr(install, "install_dir"):
            scheme["sitedir"] = install.install_dir
        scheme["prefix"] = scheme["eprefix"] = install.install_base

        return scheme

    def run(self):
        dist = self.distribution
        dist.top_node.bldnode.mkdir()

        section_writer = SectionWriter()

        scheme = self._get_install_scheme(dist.pkg)

        def build_packages(pkg):
            from bento.commands.build import _build_python_files
            return _build_python_files(dist.pkg, dist.top_node)
        def build_config_py(pkg):
            return _build_config_py(pkg.config_py, scheme, dist.top_node)
        section_writer.sections_callbacks["pythonfiles"] = build_packages
        section_writer.sections_callbacks["bentofiles"] = build_config_py

        section_writer.update_sections(dist.pkg)
        ipkg_path = dist.top_node.make_node(IPKG_PATH)
        ipkg_path.parent.mkdir()

        section_writer.store(ipkg_path.abspath(), dist.pkg)
