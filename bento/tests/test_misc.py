import os

from bento.compat.api \
    import \
        NamedTemporaryFile
from bento.compat.api.moves \
    import \
        unittest
from bento.private.bytecode \
    import \
        bcompile, PyCompileError

def run_with_tempfile(content, function, mode="w"):
    """Create a temporary file with the given content, and execute tbe
    given function after the temporary file has been closed.

    The file is guaranteed to be deleted whether function succeeds or not
    """
    f = NamedTemporaryFile(mode=mode, delete=False)
    try:
        f.write(content)
        f.close()
        return function(f.name)
    finally:
        f.close()
        os.remove(f.name)

class TestBytecode(unittest.TestCase):
    def test_sanity(self):
        s = """print("foo")"""
        run_with_tempfile(s, lambda name: bcompile(name))

    def test_invalid(self):
        s = """print("""
        def f(filename):
            self.assertRaises(PyCompileError, lambda: bcompile(filename))
        run_with_tempfile(s, f)
