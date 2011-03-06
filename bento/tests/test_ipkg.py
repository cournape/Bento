import os
import unittest

from cStringIO \
    import \
        StringIO

from bento.compat.api import json

import nose.tools

from bento.core.package \
    import \
        PackageDescription
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

        nose.tools.assert_equal(r_section.files, section.files)

def create_simple_ipkg_args():
    files = ["scripts/foo.py", "scripts/bar.py"]
    section = InstalledSection.from_source_target_directories("pythonfiles",
                    "section1", "source", "target", files)
    sections = {"pythonfiles": {"section1": section}}

    meta = ipkg_meta_from_pkg(SPHINX_META_PKG)
    return meta, sections

class TestIPKG(unittest.TestCase):
    def setUp(self):
        self.meta, self.sections = create_simple_ipkg_args()

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
        self.meta, self.sections = create_simple_ipkg_args()

    def test_simple(self):
        ipkg = InstalledPkgDescription(self.sections, self.meta, {})
        sections = ipkg.resolve_paths()
        res = sorted([(kind, source, target) for kind, source, target in iter_files(sections)])
        ref = [("pythonfiles", os.path.join("source", "scripts", "bar.py"), os.path.join("target", "scripts", "bar.py")),
               ("pythonfiles", os.path.join("source", "scripts", "foo.py"), os.path.join("target", "scripts", "foo.py"))]
        self.assertEqual(res, ref)
