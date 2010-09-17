import os
import tempfile
import shutil
from unittest import TestCase

class TmpContextBase(TestCase):
    def setUp(self):
        self.cwd = os.getcwd()
        self.d = tempfile.mkdtemp()
        os.chdir(self.d)

    def tearDown(self):
        shutil.rmtree(self.d)
