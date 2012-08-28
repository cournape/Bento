from bento.commands.registries \
    import \
        _RegistryBase
from bento.compat.api import moves

class Test_RegistryBase(moves.unittest.TestCase):
    def test_simple(self):
        registry = _RegistryBase()
        registry.register_category("dummy", lambda: 1)
        registry.register_callback("dummy", "dummy_func", lambda: 2)

        self.assertEqual(registry.callback("dummy", "dummy_func")(), 2)
        self.assertEqual(registry.callback("dummy", "non_existing_dummy_func")(), 1)

    def test_double_registration(self):
        registry = _RegistryBase()
        registry.register_category("dummy", lambda: 1)
        self.assertRaises(ValueError, lambda: registry.register_category("dummy", lambda: 2))

        self.assertEqual(registry.callback("dummy", "non_existing_dummy_func")(), 1)

    def test_missing_category(self):
        registry = _RegistryBase()
        self.assertRaises(ValueError, lambda: registry.register_callback("dummy", "dummy_func", lambda: 2))
        self.assertRaises(ValueError, lambda: registry.callback("dummy", "dummy_func"))

    def test_default_callback(self):
        registry = _RegistryBase()

        registry.register_category("dummy", lambda: 1)
        self.assertEqual(registry.default_callback("dummy"), 1)
        self.assertRaises(ValueError, lambda: registry.default_callback("non_existing_category"))
