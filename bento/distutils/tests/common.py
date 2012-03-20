import os
import os.path as op
import tempfile
import shutil

from bento.compat.api.moves \
    import \
        unittest
from bento.distutils.dist \
    import \
        BentoDistribution
from bento.distutils.commands.install \
    import \
        install
        
class DistutilsCommandTestBase(unittest.TestCase):
    def setUp(self):
        self.old_cwd = os.getcwd()
        self.new_cwd = tempfile.mkdtemp()
        try:
            os.chdir(self.new_cwd)
        except:
            os.chdir(self.old_cwd)
            shutil.rmtree(self.new_cwd)
            raise

    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.new_cwd)
