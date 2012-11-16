import os
import tempfile
import shutil

from six.moves import StringIO

from bento.compat.api \
    import \
        json
from bento.compat.api.moves \
    import \
        unittest
from bento.core.node \
    import \
        create_root_with_source_tree
from bento.testing.misc \
    import \
        create_simple_build_manifest_args
from bento.installed_package_description \
    import \
        BuildManifest, InstalledSection, iter_files

class TestInstalledSection(unittest.TestCase):
    def test_simple(self):
        files = [("scripts/foo.py", "scripts/foo"),
                 ("scripts/bar.py", "scripts/bar.py")]
        InstalledSection("pythonfiles", "section1", "source", "target", files)

    def test_from_source_target(self):
        files = [("scripts/foo.py", "scripts/foo.py"),
                 ("scripts/bar.py", "scripts/bar.py")]
        r_section = InstalledSection("pythonfiles", "section1", "source", "target", files)

        files = ["scripts/foo.py", "scripts/bar.py"]
        section = InstalledSection.from_source_target_directories("pythonfiles",
                        "section1", "source", "target", files)

        self.assertEqual(r_section.files, section.files)

class TestBUILD_MANIFEST(unittest.TestCase):
    def setUp(self):
        self.src_root = tempfile.mkdtemp()
        self.bld_root = self.src_root

        root = create_root_with_source_tree(self.src_root, self.bld_root)
        self.top_node = root.find_node(self.src_root)

        self.meta, self.sections, self.nodes = create_simple_build_manifest_args(self.top_node)

    def tearDown(self):
        shutil.rmtree(self.top_node.abspath())

    def test_simple_create(self):
        BuildManifest(self.sections, self.meta, {})

    def test_simple_roundtrip(self):
        # FIXME: we compare the loaded json to avoid dealing with encoding
        # differences when comparing objects, but this is kinda stupid
        r_build_manifest = BuildManifest(self.sections, self.meta, {})
        f = StringIO()
        r_build_manifest._write(f)
        r_s = f.getvalue()

        build_manifest = BuildManifest.from_string(r_s)
        f = StringIO()
        build_manifest._write(f)
        s = f.getvalue()
        
        self.assertEqual(json.loads(r_s), json.loads(s))

class TestIterFiles(unittest.TestCase):
    def setUp(self):
        self.src_root = tempfile.mkdtemp()
        self.bld_root = self.src_root

        root = create_root_with_source_tree(self.src_root, self.bld_root)
        self.top_node = root.find_node(self.src_root)

        self.meta, self.sections, nodes = create_simple_build_manifest_args(self.top_node)
        for n in nodes:
            print(n.abspath())

    def tearDown(self):
        shutil.rmtree(self.top_node.abspath())

    def test_simple(self):
        build_manifest = BuildManifest(self.sections, self.meta, {})
        sections = build_manifest.resolve_paths(self.top_node)
        res = sorted([(kind, source.abspath(), target.abspath()) \
                      for kind, source, target in iter_files(sections)])
        target_dir = build_manifest.resolve_path(os.path.join("$prefix", "target"))
        ref = [("pythonfiles", os.path.join(self.top_node.abspath(), "source", "scripts", "bar.py"),
                               os.path.join(target_dir, "scripts", "bar.py")),
               ("pythonfiles", os.path.join(self.top_node.abspath(), "source", "scripts", "foo.py"),
                               os.path.join(target_dir, "scripts", "foo.py"))]
        self.assertEqual(res, ref)
