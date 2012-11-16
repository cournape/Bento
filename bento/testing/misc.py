import os

import bento.testing.bentos

from bento.core.package \
    import \
        PackageDescription
from bento.installed_package_description \
    import \
        InstalledSection, build_manifest_meta_from_pkg

# FIXME: use correct install path instead of python package hack
BENTOS_DIR = os.path.dirname(bento.testing.bentos.__file__)
SPHINX_META = os.path.join(BENTOS_DIR, "sphinx_meta.info")

SPHINX_META_PKG = PackageDescription.from_file(SPHINX_META)

def create_simple_build_manifest_args(top_node):
    files = ["scripts/foo.py", "scripts/bar.py"]
    srcdir = "source"

    nodes = [top_node.make_node(os.path.join(srcdir, f)) for f in files]
    for n in nodes:
        n.parent.mkdir()
        n.write("")
    section = InstalledSection.from_source_target_directories("pythonfiles",
                    "section1", os.path.join("$_srcrootdir", srcdir), "$prefix/target", files)
    sections = {"pythonfiles": {"section1": section}}

    meta = build_manifest_meta_from_pkg(SPHINX_META_PKG)
    return meta, sections, nodes

