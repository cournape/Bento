import sys
import os
import re
import tempfile

from bento.compat.api \
    import \
        NamedTemporaryFile
from bento.compat.api.moves import unittest

# Finicky: to make sure we test our NamedTemporaryFile and not something else...
tempfile.NamedTemporaryFile = NamedTemporaryFile

def _bytes(s):
    if sys.version_info[0] < 3:
        return s
    else:
        return bytes(s.encode("ascii"))

# Code below copied verbatim from python 2.6.4 test_tempfile.py file
class TC(unittest.TestCase):

    str_check = re.compile(r"[a-zA-Z0-9_-]{6}$")

    def failOnException(self, what, ei=None):
        if ei is None:
            ei = sys.exc_info()
        self.fail("%s raised %s: %s" % (what, ei[0], ei[1]))

    def nameCheck(self, name, dir, pre, suf):
        (ndir, nbase) = os.path.split(name)
        npre  = nbase[:len(pre)]
        nsuf  = nbase[len(nbase)-len(suf):]

        # check for equality of the absolute paths!
        self.assertEqual(os.path.abspath(ndir), os.path.abspath(dir),
                         "file '%s' not in directory '%s'" % (name, dir))
        self.assertEqual(npre, pre,
                         "file '%s' does not begin with '%s'" % (nbase, pre))
        self.assertEqual(nsuf, suf,
                         "file '%s' does not end with '%s'" % (nbase, suf))

        nbase = nbase[len(pre):len(nbase)-len(suf)]
        self.assert_(self.str_check.match(nbase),
                     "random string '%s' does not match /^[a-zA-Z0-9_-]{6}$/"
                     % nbase)

class test_NamedTemporaryFile(TC):
    """Test NamedTemporaryFile()."""

    def do_create(self, dir=None, pre="", suf="", delete=True):
        if dir is None:
            dir = tempfile.gettempdir()
        try:
            file = tempfile.NamedTemporaryFile(dir=dir, prefix=pre, suffix=suf,
                                               delete=delete)
        except:
            self.failOnException("NamedTemporaryFile")

        self.nameCheck(file.name, dir, pre, suf)
        return file


    def test_basic(self):
        # NamedTemporaryFile can create files
        self.do_create()
        self.do_create(pre="a")
        self.do_create(suf="b")
        self.do_create(pre="a", suf="b")
        self.do_create(pre="aa", suf=".txt")

    def test_creates_named(self):
        # NamedTemporaryFile creates files with names
        f = tempfile.NamedTemporaryFile()
        self.failUnless(os.path.exists(f.name),
                        "NamedTemporaryFile %s does not exist" % f.name)

    def test_del_on_close(self):
        # A NamedTemporaryFile is deleted when closed
        dir = tempfile.mkdtemp()
        try:
            f = tempfile.NamedTemporaryFile(dir=dir)
            f.write(_bytes('blat'))
            f.close()
            self.failIf(os.path.exists(f.name),
                        "NamedTemporaryFile %s exists after close" % f.name)
        finally:
            os.rmdir(dir)

    def test_dis_del_on_close(self):
        # Tests that delete-on-close can be disabled
        dir = tempfile.mkdtemp()
        tmp = None
        try:
            f = tempfile.NamedTemporaryFile(dir=dir, delete=False)
            tmp = f.name
            f.write(_bytes('blat'))
            f.close()
            self.failUnless(os.path.exists(f.name),
                        "NamedTemporaryFile %s missing after close" % f.name)
        finally:
            if tmp is not None:
                os.unlink(tmp)
            os.rmdir(dir)

    def test_multiple_close(self):
        # A NamedTemporaryFile can be closed many times without error
        f = tempfile.NamedTemporaryFile()
        f.write(_bytes('abc\n'))
        f.close()
        try:
            f.close()
            f.close()
        except:
            self.failOnException("close")
