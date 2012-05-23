import os
import tempfile
import sys

from bento.compat.api.moves \
    import \
        unittest
from bento.core.pkg_objects \
    import \
        DataFiles, Executable

class TestDataFiles(unittest.TestCase):
    def test_simple(self):
        data = DataFiles("data", files=["foo.c"])
        self.assertEqual(data.name, "data")
        self.assertEqual(data.files, ["foo.c"])
        self.assertEqual(data.source_dir, ".")
        self.assertEqual(data.target_dir, "$sitedir")

    def test_from_dict(self):
        parsed_dict = {"name": "data",
                       "files": ["foo.c", "yo.c"], "target_dir": "foo"}
        data = DataFiles.from_parse_dict(parsed_dict)
        self.assertEqual(data.name, "data")
        self.assertEqual(data.files, ["foo.c", "yo.c"])
        self.assertEqual(data.target_dir, "foo")
    # TODO: test with a populated temp dir

class TestExecutable(unittest.TestCase):
    def test_basic(self):
        exe = Executable.from_representation("foo = core:main")
        self.assertEqual(exe.name, "foo")
        self.assertEqual(exe.module, "core")
        self.assertEqual(exe.function, "main")

        self.assertEqual(exe.full_representation(), "foo = core:main")
