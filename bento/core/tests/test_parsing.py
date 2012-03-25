import os
import tempfile
import stat

import os.path as op

from bento.compat.api.moves \
    import \
        unittest
from bento.core.pkg_objects \
    import \
        PathOption, FlagOption, DataFiles
from bento.core.options \
    import \
        PackageOptions

from bento.core.utils \
    import \
        extract_exception
from bento \
    import \
        PackageDescription
from bento.compat.api \
    import \
        NamedTemporaryFile
from bento.core.errors \
    import \
        BentoError
from bento.core.parser.errors \
    import \
        ParseError

from bento.core.parser import parser as parser_module

#old = sys.path[:]
#try:
#    sys.path.insert(0, join(dirname(__file__), "pkgdescr"))
#    from simple_package import PKG, DESCR
#finally:
#    sys.path = old

class TestParseError(unittest.TestCase):
    def setUp(self):
        self.f = NamedTemporaryFile(mode="w", delete=False)

    def tearDown(self):
        self.f.close()
        os.remove(self.f.name)

    def test_simple(self):
        text = """\
NName: foo
"""
        self.assertRaises(ParseError, lambda : PackageDescription.from_string(text))

        try:
            PackageDescription.from_string(text)
            raise AssertionError("Should raise here !")
        except ParseError:
            e = extract_exception()
            self.assertEqual(str(e), "yacc: Syntax error at line 1, Token(WORD, 'NName')")

    def test_simple_filename(self):
        f = self.f
        f.write("NName: foo")
        f.flush()
        self.assertRaises(ParseError, lambda : PackageDescription.from_file(f.name))

    def test_error_string(self):
        f = self.f
        f.write("NName: foo")
        f.flush()
        try:
            PackageDescription.from_file(f.name)
            raise AssertionError("Should raise here !")
        except ParseError:
            e = extract_exception()
            self.assertEqual(str(e), """\
  File "%s", line 1
NName: foo
^
Syntax error""" % f.name)

class TestDataFiles(unittest.TestCase):
    def test_simple(self):
        text = """\
Name: foo

DataFiles: data
    TargetDir: $datadir
    Files:
        foo.data
"""
        r_data = DataFiles("data", files=["foo.data"], target_dir="$datadir")
        pkg = PackageDescription.from_string(text)
        self.failUnless("data" in pkg.data_files)
        self.assertEqual(pkg.data_files["data"].__dict__, r_data.__dict__)
    
class TestOptions(unittest.TestCase):
    simple_text = """\
Name: foo

Flag: flag1
    Description: flag1 description
    Default: false

Path: foo
    Description: foo description
    Default: /usr/lib
"""
    def _test_simple(self, opts):
        self.failUnless(opts.name, "foo")

        flag = FlagOption("flag1", "false", "flag1 description")
        self.failUnless(opts.flag_options.keys(), ["flags"])
        self.failUnless(opts.flag_options["flag1"], flag.__dict__)

        path = PathOption("foo", "/usr/lib", "foo description")
        self.failUnless(opts.path_options.keys(), ["foo"])
        self.failUnless(opts.path_options["foo"], path.__dict__)

    def test_simple_from_string(self):
        s = self.simple_text
        opts = PackageOptions.from_string(s)
        self._test_simple(opts)

    def test_simple_from_file(self):
        fid, filename = tempfile.mkstemp(suffix=".info", text=True)
        try:
            os.write(fid, self.simple_text.encode())
            opts = PackageOptions.from_file(filename)
            self._test_simple(opts)
        finally:
            os.close(fid)
            os.remove(filename)

class TestParserCaching(unittest.TestCase):
    def setUp(self):
        wdir = tempfile.mkdtemp()
        self.subwdir= "bar"
        self.old = os.getcwd()
        os.chdir(wdir)

    def tearDown(self):
        os.chdir(self.old)

    def test_no_cached_failure(self):
        """Ensure we raise an error when the cached parser file does not exists
        and we cannot create one."""
        os.makedirs(self.subwdir)
        os.chmod(self.subwdir, stat.S_IREAD | stat.S_IEXEC)
        parsetab = op.join(self.subwdir, "parsetab")

        old_parsetab = parser_module._PICKLED_PARSETAB
        try:
            parser_module._PICKLED_PARSETAB = parsetab
            try:
                parser_module.Parser()
                self.assertTrue(len(self._list_files()) == 0, "Ply created a cached file in CWD")
                self.fail("Expected an error when creating a parser in read-only dir !")
            except BentoError:
                pass
        finally:
            parser_module._PICKLED_PARSETAB = old_parsetab

    def _list_files(self):
        """Return the list of files in cwd (including subdirectories)."""
        created_files = []
        for root, dirs, files in os.walk(os.getcwd()):
            created_files.extend([op.join(root, f) for f in files])
        return created_files

    def test_read_only_cached(self):
        """Test that we can create a parser backed by a read-only parsetab
        file."""
        os.makedirs(self.subwdir)
        parsetab = op.join(self.subwdir, "parsetab")

        old_parsetab = parser_module._PICKLED_PARSETAB
        try:
            parser_module._PICKLED_PARSETAB = parsetab
            parser_module.Parser()
            self.assertEqual(self._list_files(), [op.abspath(parsetab)])

            os.chmod(self.subwdir, stat.S_IREAD | stat.S_IEXEC)
            os.chmod(parsetab, stat.S_IREAD)

            parser_module.Parser()
            # This ensures ply did not write another cached file behind our back
            self.assertEqual(self._list_files(), [op.abspath(parsetab)],
                             "Ply created another cached parsetab file !")
        finally:
            parser_module._PICKLED_PARSETAB = old_parsetab
