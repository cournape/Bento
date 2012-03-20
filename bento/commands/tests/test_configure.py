import os
import shutil
import tempfile

from bento.compat.api.moves \
    import \
        unittest

from bento.core.node \
    import \
        create_root_with_source_tree
from bento.commands.tests.utils \
    import \
        prepare_configure
from bento.commands.context \
    import \
        ConfigureYakuContext

BENTO_INFO = """\
Name: Sphinx
Version: 0.6.3
Summary: Python documentation generator
Url: http://sphinx.pocoo.org/
DownloadUrl: http://pypi.python.org/pypi/Sphinx
Description: Some long description.
Author: Georg Brandl
AuthorEmail: georg@python.org
Maintainer: Georg Brandl
MaintainerEmail: georg@python.org
License: BSD
"""

class TestConfigureCommand(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.root = create_root_with_source_tree(self.d, os.path.join(self.d, "build"))

        self.old_dir = os.getcwd()
        os.chdir(self.d)

    def tearDown(self):
        os.chdir(self.old_dir)
        shutil.rmtree(self.d)

    def test_simple(self):
        root = self.root
        run_node = root.find_node(self.d)

        conf, configure = prepare_configure(run_node, BENTO_INFO, ConfigureYakuContext)
        configure.run(conf)
        configure.shutdown(conf)
        conf.shutdown()

    def test_flags(self):
        bento_info = """\
Name: foo

Flag: floupi
    Description: some floupi flag
    Default: true
"""
        run_node = self.root.find_node(self.d)

        conf, configure = prepare_configure(run_node, bento_info, ConfigureYakuContext, ["--floupi=false"])
        configure.run(conf)
        configure.shutdown(conf)
        conf.shutdown()
