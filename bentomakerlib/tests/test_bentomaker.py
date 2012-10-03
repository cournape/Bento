import os
import sys
import tempfile
import shutil

import os.path as op

import mock
import multiprocessing

from bento.compat.api.moves \
    import \
        unittest
from bento.core.node \
    import \
        create_base_nodes
from bento.utils.utils \
    import \
        extract_exception
from bento.commands.contexts \
    import \
        GlobalContext
from bento.testing.decorators \
    import \
         disable_missing_bento_warning
from bento.testing.sub_test_case \
    import \
         SubprocessTestCase
from bento.errors \
    import \
        UsageException, CommandExecutionFailure, ConvertionError, ParseError

import bentomakerlib.bentomaker
import bento.commands.build_yaku
from bento.compat.dist \
    import \
        DistributionMetadata

from bentomakerlib.bentomaker \
    import \
        main, noexc_main, _wrapped_main, parse_global_options, create_global_options_context

# FIXME: nose is broken - needed to make it happy
if sys.platform == "darwin":
    import bento.commands.build_mpkg
# FIXME: nose is broken - needed to make it happy
# FIXME: nose is broken - needed to make it happy

class Common(unittest.TestCase):
    def setUp(self):
        super(Common, self).setUp()

        self.d = tempfile.mkdtemp()
        self.old = os.getcwd()

        try:
            os.chdir(self.d)
            self.top_node, self.build_node, self.run_node = \
                create_base_nodes(self.d, op.join(self.d, "build"), self.d)
        except:
            os.chdir(self.old)
            shutil.rmtree(self.d)

    def tearDown(self):
        os.chdir(self.old)
        shutil.rmtree(self.d)
        super(Common, self).tearDown()

class TestSpecialCommands(Common):
    @disable_missing_bento_warning
    def test_help_globals(self):
        main(["help", "globals"])

    @disable_missing_bento_warning
    def test_help_commands(self):
        main(["help", "commands"])

    def test_global_options_version(self):
        main(["--version"])

    def test_global_options_full_version(self):
        main(["--full-version"])

    def test_usage(self):
        main(["--help"])

    @disable_missing_bento_warning
    def test_command_help(self):
        main(["configure", "--help"])

class TestMain(Common):
    def test_no_bento(self):
        main([])

    @disable_missing_bento_warning
    def test_help_non_existing_command(self):
        self.assertRaises(UsageException, lambda: main(["help", "floupi"]))

    def test_configure_help(self):
        bento_info = """\
Name: foo
"""
        self.top_node.make_node("bento.info").write(bento_info)
        main(["configure", "--help"])

    def test_help_command(self):
        bento_info = """\
Name: foo
"""
        self.top_node.make_node("bento.info").write(bento_info)
        main(["help", "configure"])

    def test_configure(self):
        bento_info = """\
Name: foo
"""
        self.top_node.make_node("bento.info").write(bento_info)
        main(["configure"])

class TestMainCommands(Common):
    def setUp(self):
        super(TestMainCommands, self).setUp()

        bento_info = """\
Name: foo
"""
        self.top_node.make_node("bento.info").write(bento_info)

    def tearDown(self):
        super(TestMainCommands, self).tearDown()

    def test_configure(self):
        main(["configure"])

    def test_build(self):
        main(["build"])

    def test_install(self):
        main(["install"])

    def test_sdist(self):
        main(["sdist"])

    def test_build_egg(self):
        main(["build_egg"])

    @unittest.skipIf(sys.platform != "win32", "wininst is win32-only test")
    def test_wininst(self):
        main(["build_wininst"])

    @unittest.skipIf(sys.platform != "darwin", "mpkg is darwin-only test")
    def test_mpkg(self):
        main(["build_mpkg"])

# Add SubprocessTestCase mixin as convert depends on distutils which uses
# globals
class TestConvertCommand(Common, SubprocessTestCase):
    def test_convert(self):
        self.top_node.make_node("setup.py").write("""\
from distutils.core import setup

setup(name="foo")
""")
        main(["convert"])
        n = self.top_node.find_node("bento.info")
        r_bento = """\
Name: foo
Version: 0.0.0
Summary: UNKNOWN
Url: UNKNOWN
DownloadUrl: UNKNOWN
Description: UNKNOWN
Author: UNKNOWN
AuthorEmail: UNKNOWN
Maintainer: UNKNOWN
MaintainerEmail: UNKNOWN
License: UNKNOWN
Platforms: UNKNOWN

ExtraSourceFiles:
    setup.py
"""
        self.assertEqual(n.read(), r_bento)

class TestRunningEnvironment(Common):
    def test_in_sub_directory(self):
        bento_info = """\
Name: foo
"""
        self.top_node.make_node("bento.info").write(bento_info)

        subdir_node = self.top_node.make_node("subdir")
        subdir_node.mkdir()

        try:
            os.chdir(subdir_node.abspath())
            self.assertRaises(UsageException, lambda: main(["--bento-info=../bento.info", "configure"]))
        finally:
            os.chdir(self.top_node.abspath())

class TestCommandData(Common):
    def test_simple(self):
        # We use subprocesses to emulate how bentomaker would run itself - this
        # is more of a functional test than a unit test.
        bento_info = """\
Name: foo
"""
        self.top_node.make_node("bento.info").write(bento_info)

        p = multiprocessing.Process(target=noexc_main, args=(['configure', '--prefix=/fubar'],))
        p.start()
        p.join()

        def check_cmd_data(q):
            from bentomakerlib.bentomaker \
                import \
                    CMD_DATA_DUMP
            from bento.utils.utils \
                import \
                    read_or_create_dict

            cmd_data_db = self.build_node.find_node(CMD_DATA_DUMP)
            if cmd_data_db is None:
                raise IOError()
            cmd_data_store = read_or_create_dict(cmd_data_db.abspath())
            q.put(cmd_data_store.get("configure", []))

        q = multiprocessing.Queue()
        p = multiprocessing.Process(target=check_cmd_data, args=(q,))
        p.start()
        self.assertEqual(q.get(timeout=1), ["--prefix=/fubar"])
        p.join()

    def test_flags(self):
        """Test that flag value specified on the command line are correctly
        stored between run."""
        # We use subprocesses to emulate how bentomaker would run itself - this
        # is more of a functional test than a unit test.
        bento_info = """\
Name: foo

Flag: debug
    Description: debug flag
    Default: true

HookFile: bscript

Library:
    if flag(debug):
        Modules: foo
    else:
        Modules: bar
"""
        self.top_node.make_node("bento.info").write(bento_info)
        self.top_node.make_node("bscript").write("""\
import sys
from bento.commands import hooks

@hooks.pre_build
def pre_build(context):
    if not context.pkg.py_modules == ['bar']:
        sys.exit(57)
""")
        self.top_node.make_node("foo.py").write("")
        self.top_node.make_node("bar.py").write("")

        p = multiprocessing.Process(target=main, args=(['configure', '--debug=false'],))
        p.start()
        p.join()

        p = multiprocessing.Process(target=main, args=(['build'],))
        p.start()
        p.join()

        self.assertEqual(p.exitcode, 0)

def raise_function(klass):
    raise klass()

class TestBentomakerError(Common):
    @mock.patch("bentomakerlib.bentomaker.pprint", lambda color, s, fout=None: None)
    def test_simple(self):
        errors = (
            (UsageException, 2),
            (ParseError, 2),
            (ConvertionError, 2),
            (CommandExecutionFailure, 2),
            (bento.errors.ConfigurationError, 2),
            (bento.errors.BuildError, 2),
            (bento.errors.InvalidPackage, 2),
            (Exception, 1),
        )
        for klass, error_code in errors:
            old_main = bentomakerlib.bentomaker.main
            bentomakerlib.bentomaker.main = lambda argv: raise_function(klass)
            try:
                try:
                    noexc_main()
                except SystemExit:
                    e = extract_exception()
                    self.assertEqual(e.code, error_code,
                                     "Expected error code %d for exception type(%r)" % \
                                             (error_code, klass))
            finally:
                bentomakerlib.bentomaker.main = old_main

class TestStartupHook(Common):
    def setUp(self):
        super(TestStartupHook, self).setUp()

        bento_info = """\
Name: foo

HookFile: bscript
"""
        self.top_node.make_node("bento.info").write(bento_info)

    def test_simple(self):
        bscript = """\
from bento.commands import hooks

@hooks.startup
def startup(context):
    context.seen = True
"""
        self.top_node.make_node("bscript").write(bscript)

        global_context = GlobalContext(None)
        options_context = create_global_options_context()
        popts = parse_global_options(options_context, ["configure"])

        _wrapped_main(global_context, popts, self.run_node, self.top_node,
                self.build_node)
        self.assertTrue(getattr(global_context, "seen", False))

    def test_register_command(self):
        bscript = """\
from bento.commands import hooks
from bento.commands.core import Command

@hooks.startup
def startup(context):
    context.register_command("foo", Command())
"""
        self.top_node.make_node("bscript").write(bscript)

        global_context = GlobalContext(None)
        options_context = create_global_options_context()
        popts = parse_global_options(options_context, ["configure"])

        _wrapped_main(global_context, popts, self.run_node, self.top_node,
                self.build_node)
        self.assertTrue(global_context.is_command_registered("foo"))

    def test_register_command_with_options(self):
        bscript = """\
from bento.commands import hooks
from bento.commands.core import Command
from bento.commands.options import OptionsContext, Option

class DocCommand(Command):
    def run(self, context):
        pass

@hooks.startup
def startup(context):
    cmd = DocCommand()
    context.register_command("doc", cmd)

    options_context = OptionsContext.from_command(cmd)
    options_context.add_option(Option("--some-weird-option"))
    context.register_options_context("doc", options_context)
"""
        self.top_node.make_node("bscript").write(bscript)

        global_context = GlobalContext(None)
        options_context = create_global_options_context()
        popts = parse_global_options(options_context, ["doc"])

        _wrapped_main(global_context, popts, self.run_node, self.top_node,
                self.build_node)
        p = global_context.retrieve_options_context("doc").parser
        o, a = p.parse_args(["--some-weird-option=46"])
        self.assertEqual(o.some_weird_option, "46")


    def test_register_existing_command(self):
        bscript = """\
from bento.commands import hooks
from bento.commands.core import Command

@hooks.startup
def startup(context):
    context.register_command("configure", Command)
"""
        self.top_node.make_node("bscript").write(bscript)

        global_context = GlobalContext(None)
        options_context = create_global_options_context()
        popts = parse_global_options(options_context, ["configure"])

        self.assertRaises(ValueError, _wrapped_main,
                          global_context, popts, self.run_node, self.top_node,
                           self.build_node)
