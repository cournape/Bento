from bento.compat.api.moves \
    import \
        unittest

from bento.backends.utils \
    import \
        load_backend

class TestLoadBackend(unittest.TestCase):
    def test_simple(self):
        for backend in ("Distutils", "Yaku"):
            load_backend(backend)
