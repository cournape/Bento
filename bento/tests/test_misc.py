import os
import unittest

from nose.tools \
    import \
        assert_raises

from bento.compat.api \
    import \
        NamedTemporaryFile
from bento.private.bytecode \
    import \
        bcompile, PyCompileError

class TestBytecode(unittest.TestCase):
    def test_sanity(self):
        f = NamedTemporaryFile(mode="w")
        try:
            s = """print("foo")"""
            f.write(s)
            f.flush()
            code = bcompile(f.name)
        finally:
            f.close()

    def test_invalid(self):
        f = NamedTemporaryFile(mode="w")
        try:
            s = """print("""
            f.write(s)
            f.flush()
            assert_raises(PyCompileError, lambda: bcompile(f.name))
        finally:
            f.close()
