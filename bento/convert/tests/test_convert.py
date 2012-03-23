import os
import sys

from bento.misc.testing \
    import \
        SubprocessTestCase
from bento.core.node \
    import \
        create_first_node
from bento.convert.core \
    import \
        monkey_patch

class TestMonkeyPatch(SubprocessTestCase):
    def setUp(self):
        self.top_node = create_first_node(os.getcwd())

    def test_distutils(self):
        monkey_patch(self.top_node, "distutils", "setup.py")
        self.assertTrue("setuptools" not in sys.modules)

    def test_setuptools(self):
        monkey_patch(self.top_node, "setuptools", "setup.py")
        self.assertTrue("setuptools" in sys.modules)

#class TestMonkeyPatch(SubprocessTestCase):
