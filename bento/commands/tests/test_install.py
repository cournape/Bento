import os
import shutil
import tempfile
import os.path as op

from bento.compat.api.moves \
    import \
        unittest

from bento.core.node \
    import \
        create_root_with_source_tree

from bento.commands.context \
    import \
        ConfigureYakuContext, CmdContext
from bento.commands.tests.utils \
    import \
        prepare_configure, prepare_build
from bento.commands.install \
    import \
        InstallCommand, TransactionLog, rollback_transaction
from bento.commands.options \
    import \
        OptionsContext

from bento.core.testing \
    import \
        create_fake_package_from_bento_info, require_c_compiler

class TestBuildCommand(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.root = create_root_with_source_tree(self.d, os.path.join(self.d, "build"))
        self.top_node = self.root.find_node(self.d)

        self.old_dir = os.getcwd()
        os.chdir(self.d)

    def tearDown(self):
        os.chdir(self.old_dir)
        shutil.rmtree(self.d)

    def _run_configure_and_build(self, bento_info, install_prefix):
        top_node = self.top_node

        create_fake_package_from_bento_info(top_node, bento_info)

        cmd_argv = ["--prefix=%s" % install_prefix, "--exec-prefix=%s" % install_prefix]

        conf, configure = prepare_configure(top_node, bento_info, ConfigureYakuContext, cmd_argv)
        configure.run(conf)
        conf.shutdown()

        bld, build = prepare_build(top_node, conf.pkg, conf.package_options)
        build.run(bld)
        build.shutdown(bld)

        return conf, configure, bld, build

    def _test_dry_run(self, bento_info):
        install_prefix = tempfile.mkdtemp()
        try:
            conf, configure, bld, build = self._run_configure_and_build(bento_info, install_prefix)

            install = InstallCommand()
            opts = OptionsContext.from_command(install)

            inst = CmdContext(None, ["--list-files"], opts, conf.pkg, self.top_node)
            install.run(inst)
        finally:
            shutil.rmtree(install_prefix)

    def _test_run(self, bento_info):
        install_prefix = tempfile.mkdtemp()
        try:
            conf, configure, bld, build = self._run_configure_and_build(bento_info, install_prefix)

            install = InstallCommand()
            opts = OptionsContext.from_command(install)

            inst = CmdContext(None, [], opts, conf.pkg, self.top_node)
            install.run(inst)
        finally:
            shutil.rmtree(install_prefix)

    def test_simple(self):
        """Test whether install runs at all for a trivial package."""
        bento_info = """\
Name: foo

Library:
    Packages: foo, foo.bar
    Modules: fubar
"""
        self._test_run(bento_info)

    def test_simple_list_only(self):
        """Test whether install runs at all for a trivial package."""
        bento_info = """\
Name: foo

Library:
    Packages: foo, foo.bar
    Modules: fubar
"""
        self._test_dry_run(bento_info)

    @require_c_compiler()
    def test_simple_extension_list_only(self):
        """Test whether install runs at all for a trivial package."""
        bento_info = """\
Name: foo

Library:
    Packages: foo, foo.bar
    Modules: fubar
    Extension: foo
        Sources: src/foo.c
"""
        self._test_dry_run(bento_info)

def write_simple_tree(base_dir):
    """Write some files and subdirectories in base_dir."""
    files = []
    cur_dir = base_dir
    for i in range(25):
        if i % 3 == 0:
            cur_dir = op.join(cur_dir, "dir%d" % i)
            os.makedirs(cur_dir)
        filename = op.join(cur_dir, "foo%s.txt" % i)
        fid = open(filename, "wt")
        try:
            fid.write("file %d" % i)
        finally:
            fid.close()
        files.append(filename)
    return files

class TestTransactionLog(unittest.TestCase):
    def setUp(self):
        self.base_dir = tempfile.mkdtemp()
        self.files = write_simple_tree(self.base_dir)

    def tearDown(self):
        shutil.rmtree(self.base_dir)

    def test_simple(self):
        """Test a simple, uninterrupted run."""
        target_prefix = op.join(self.base_dir, "foo")
        trans_file = op.join(self.base_dir, "trans.log")
        self._test_simple(target_prefix, trans_file)

    def _test_simple(self, target_prefix, trans_file):
        targets = []
        log = TransactionLog(trans_file)
        try:
            for source in self.files:
                target = op.join(target_prefix, op.basename(source))
                targets.append(target)
                log.copy(source, target, None)
        finally:
            log.close()

        for target in targets:
            self.assertTrue(op.exists(target))

    def test_rollback_transaction(self):
        target_prefix = op.join(self.base_dir, "foo")
        trans_file = op.join(self.base_dir, "trans.log")

        self._test_simple(target_prefix, trans_file)

        rollback_transaction(trans_file)
        self.assertFalse(op.exists(target_prefix))

    def test_simple_interrupted(self):
        """Test a simple, interrupted run."""
        class _InterruptException(Exception):
            pass

        target_prefix = op.join(self.base_dir, "foo")

        trans_file = op.join(self.base_dir, "trans.log")
        targets = []
        log = TransactionLog(trans_file)
        try:
            try:
                for i, source in enumerate(self.files):
                    if i > len(self.files) / 3:
                        raise _InterruptException()
                    target = op.join(target_prefix, op.basename(source))
                    targets.append(target)
                    log.copy(source, target, None)
            except _InterruptException:
                log.rollback()
                for target in targets:
                    self.assertFalse(op.exists(target))
                return
            self.fail("Expected failure at this point !")
        finally:
            log.close()
