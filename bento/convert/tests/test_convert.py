import sys

from bento.misc.testing \
    import \
        SubprocessTestCase

from bento.convert.core \
    import \
        monkey_patch

class TestMonkeyPatch(SubprocessTestCase):
    def test_distutils(self):
        monkey_patch("distutils", "setup.py")
        self.assertTrue("setuptools" not in sys.modules)

    def test_setuptools(self):
        monkey_patch("setuptools", "setup.py")
        self.assertTrue("setuptools" in sys.modules)
