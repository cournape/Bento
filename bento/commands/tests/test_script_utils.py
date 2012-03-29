import os
import tempfile

import os.path as op

import mock

from bento.core.node \
    import \
        create_base_nodes
from bento.core.pkg_objects \
    import \
        Executable
from bento.compat.api.moves \
    import \
        unittest
from bento.commands.script_utils \
    import \
        nt_quote_arg, create_win32_script, create_posix_script, create_scripts

class TestMisc(unittest.TestCase):
    def test_nt_quote_arg(self):
        s = nt_quote_arg("foo")
        self.assertEqual(s, "foo")

        s = nt_quote_arg(" foo")
        self.assertEqual(s, '" foo"')

        s = nt_quote_arg("\ foo")
        self.assertEqual(s, '"\\ foo"')

class TestCreateScript(unittest.TestCase):
    def setUp(self):
        super(TestCreateScript, self).setUp()

        self.old_cwd = os.getcwd()
        self.d = tempfile.mkdtemp()

        try:
            os.chdir(self.d)
            self.top_node, self.build_node, self.run_node = create_base_nodes(self.d, op.join(self.d, "build"))
            self.build_node.mkdir()
        except:
            os.chdir(self.old_cwd)

    def tearDown(self):
        os.chdir(self.old_cwd)
        super(TestCreateScript, self).tearDown()

    def _test_create_script(self, func, executable, r_list):
        nodes = func("foo", executable, self.build_node)
        self.assertEqual(set(self.build_node.listdir()), set(r_list))
        self.assertEqual(set([node.path_from(self.build_node) for node in nodes]), set(r_list))

    def _test_create_scripts(self, executable, r_list):
        res = create_scripts({"foo": executable}, self.build_node)
        nodes = res["foo"]
        self.assertEqual(set(self.build_node.listdir()), set(r_list))
        self.assertEqual(set([node.path_from(self.build_node) for node in nodes]), set(r_list))

    @mock.patch("sys.platform", "win32")
    def test_create_script_on_win32(self):
        r_list = set(["foo-script.py", "foo.exe", "foo.exe.manifest"])
        executable = Executable("foo", "foo.bar", "fubar")
        self._test_create_scripts(executable, r_list)

    @mock.patch("sys.platform", "darwin")
    def test_create_script_on_posix(self):
        r_list = set(["foo"])
        executable = Executable("foo", "foo.bar", "fubar")
        self._test_create_scripts(executable, r_list)

    def test_create_posix_script(self):
        r_list = ["foo"]
        executable = Executable("foo", "foo.bar", "fubar")
        self._test_create_script(create_posix_script, executable, r_list)

    def test_create_win32_script(self):
        executable = Executable("foo", "foo.bar", "fubar")
        r_list = set(["foo-script.py", "foo.exe", "foo.exe.manifest"])
        self._test_create_script(create_win32_script, executable, r_list)
