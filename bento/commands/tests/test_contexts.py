import sys

from bento.commands.contexts \
    import \
        GlobalContext
from bento.compat.api.moves \
    import \
        unittest
from bento.core.options \
    import \
        PackageOptions
from bento.core.platforms \
    import \
        get_scheme

class TestGlobalContextCustomizedOptions(unittest.TestCase):
    def setUp(self):
        self.context = GlobalContext(None)
        self.maxDiff = None

    def _test(self, package_options, r_scheme):
        self.context.register_package_options(package_options)
        scheme = self.context.retrieve_scheme()

        default_scheme, _ = get_scheme(sys.platform)
        r_scheme.update(default_scheme)
        r_scheme['py_version_short'] = ".".join(str(part) for part in sys.version_info[:2])
        r_scheme['pkgname'] = package_options.name

        self.assertEqual(scheme, r_scheme)

    def test_no_options(self):
        package_options = PackageOptions.from_string("""\
Name: foo
""")
        self._test(package_options, {})

    def test_path_option(self):
        package_options = PackageOptions.from_string("""\
Name: foo

Path: floupi
    Description: yoyo
    Default: /yeah
""")
        self._test(package_options, {"floupi": "/yeah"})
