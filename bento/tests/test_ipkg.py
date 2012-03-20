import os
import sys
import tempfile
import shutil

if sys.version_info[0] < 3:
    from cStringIO import StringIO
else:
    from io import StringIO

from bento.compat.api \
    import \
        json
from bento.compat.api.moves \
    import \
        unittest

from bento.core.package \
    import \
        PackageDescription
from bento.core.utils \
    import \
        subst_vars
from bento.core.node \
    import \
        create_root_with_source_tree
from bento.installed_package_description \
    import \
        InstalledPkgDescription, InstalledSection, ipkg_meta_from_pkg, iter_files

import bento.tests.bentos

# FIXME: use correct install path instead of python package hack
BENTOS_DIR = os.path.dirname(bento.tests.bentos.__file__)
SPHINX_META = os.path.join(BENTOS_DIR, "sphinx_meta.info")

SPHINX_META_PKG = PackageDescription.from_file(SPHINX_META)

class TestInstalledSection(unittest.TestCase):
    def test_simple(self):
        files = [("scripts/foo.py", "scripts/foo"),
                 ("scripts/bar.py", "scripts/bar.py")]
        section = InstalledSection("pythonfiles", "section1", "source", "target", files)

    def test_from_source_target(self):
        files = [("scripts/foo.py", "scripts/foo.py"),
                 ("scripts/bar.py", "scripts/bar.py")]
        r_section = InstalledSection("pythonfiles", "section1", "source", "target", files)

        files = ["scripts/foo.py", "scripts/bar.py"]
        section = InstalledSection.from_source_target_directories("pythonfiles",
                        "section1", "source", "target", files)

        self.assertEqual(r_section.files, section.files)

def create_simple_ipkg_args(top_node):
    files = ["scripts/foo.py", "scripts/bar.py"]
    srcdir = "source"

    nodes = [top_node.make_node(os.path.join(srcdir, f)) for f in files]
    for n in nodes:
        n.parent.mkdir()
        n.write("")
    section = InstalledSection.from_source_target_directories("pythonfiles",
                    "section1", os.path.join("$_srcrootdir", srcdir), "$prefix/target", files)
    sections = {"pythonfiles": {"section1": section}}

    meta = ipkg_meta_from_pkg(SPHINX_META_PKG)
    return meta, sections, nodes

class TestIPKG(unittest.TestCase):
    def setUp(self):
        self.src_root = tempfile.mkdtemp()
        self.bld_root = self.src_root

        root = create_root_with_source_tree(self.src_root, self.bld_root)
        self.top_node = root.find_node(self.src_root)

        self.meta, self.sections, self.nodes = create_simple_ipkg_args(self.top_node)

    def tearDown(self):
        shutil.rmtree(self.top_node.abspath())

    def test_simple_create(self):
        ipkg = InstalledPkgDescription(self.sections, self.meta, {})

    def test_simple_roundtrip(self):
        # FIXME: we compare the loaded json to avoid dealing with encoding
        # differences when comparing objects, but this is kinda stupid
        r_ipkg = InstalledPkgDescription(self.sections, self.meta, {})
        f = StringIO()
        r_ipkg._write(f)
        r_s = f.getvalue()

        ipkg = InstalledPkgDescription.from_string(r_s)
        f = StringIO()
        ipkg._write(f)
        s = f.getvalue()
        
        self.assertEqual(json.loads(r_s), json.loads(s))

class TestIterFiles(unittest.TestCase):
    def setUp(self):
        self.src_root = tempfile.mkdtemp()
        self.bld_root = self.src_root

        root = create_root_with_source_tree(self.src_root, self.bld_root)
        self.top_node = root.find_node(self.src_root)

        self.meta, self.sections, nodes = create_simple_ipkg_args(self.top_node)
        for n in nodes:
            print(n.abspath())

    def tearDown(self):
        shutil.rmtree(self.top_node.abspath())

    def test_simple(self):
        ipkg = InstalledPkgDescription(self.sections, self.meta, {})
        sections = ipkg.resolve_paths(self.top_node)
        res = sorted([(kind, source.abspath(), target.abspath()) \
                      for kind, source, target in iter_files(sections)])
        target_dir = ipkg.resolve_path(os.path.join("$prefix", "target"))
        ref = [("pythonfiles", os.path.join(self.top_node.abspath(), "source", "scripts", "bar.py"),
                               os.path.join(target_dir, "scripts", "bar.py")),
               ("pythonfiles", os.path.join(self.top_node.abspath(), "source", "scripts", "foo.py"),
                               os.path.join(target_dir, "scripts", "foo.py"))]
        self.assertEqual(res, ref)
