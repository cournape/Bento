import os
import sys
import shutil
import tempfile

import mock

from bento.compat.api.moves \
    import \
        unittest

from bento.core.options \
    import \
        PackageOptions
from bento.core \
    import \
        PackageDescription
from bento.core.node \
    import \
        create_root_with_source_tree
from bento.commands.tests.utils \
    import \
        prepare_configure
from bento.commands.context \
    import \
        ConfigureYakuContext
from bento.commands.configure \
    import \
        _compute_scheme, set_scheme_unix

BENTO_INFO = """\
Name: Sphinx
Version: 0.6.3
Summary: Python documentation generator
Url: http://sphinx.pocoo.org/
DownloadUrl: http://pypi.python.org/pypi/Sphinx
Description: Some long description.
Author: Georg Brandl
AuthorEmail: georg@python.org
Maintainer: Georg Brandl
MaintainerEmail: georg@python.org
License: BSD
"""

class TestConfigureCommand(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.root = create_root_with_source_tree(self.d, os.path.join(self.d, "build"))

        self.old_dir = os.getcwd()
        os.chdir(self.d)

    def tearDown(self):
        os.chdir(self.old_dir)
        shutil.rmtree(self.d)

    def test_simple(self):
        root = self.root
        run_node = root.find_node(self.d)

        conf, configure = prepare_configure(run_node, BENTO_INFO, ConfigureYakuContext)
        configure.run(conf)
        configure.shutdown(conf)
        conf.shutdown()

    def test_flags(self):
        bento_info = """\
Name: foo

Flag: floupi
    Description: some floupi flag
    Default: true
"""
        run_node = self.root.find_node(self.d)

        conf, configure = prepare_configure(run_node, bento_info, ConfigureYakuContext, ["--floupi=false"])
        configure.run(conf)
        configure.shutdown(conf)
        conf.shutdown()

UNIX_REFERENCE = {
        'destdir': "/",
        'prefix': None,
        'eprefix': None,
        'bindir': '$eprefix/bin',
        'sbindir': '$eprefix/sbin',
        'libexecdir': '$eprefix/libexec',
        'sysconfdir': '$prefix/etc',
        'sharedstatedir': '$prefix/com',
        'localstatedir': '$prefix/var',
        'libdir': '$eprefix/lib',
        'includedir': '$prefix/include',
        'datarootdir': '$prefix/share',
        'datadir': '$datarootdir',
        'mandir': '$datarootdir/man',
        'infodir': '$datarootdir/info',
        'localedir': '$datarootdir/locale',
        'docdir': '$datarootdir/doc/$pkgname',
        'htmldir': '$docdir',
        'dvidir': '$docdir',
        'psdir': '$docdir',
        'pdfdir': '$docdir',
        'sitedir': '$libdir/python$py_version_short/site-packages',
        'pkgdatadir': '$datadir/$pkgname'
}

MOCK_DEBIAN_SCHEME = {
        'purelib': '$base/local/lib/python$py_version_short/dist-packages',
        'headers': '$base/local/include/python$py_version_short/$dist_name',
        'scripts': '$base/local/bin',
}


class TestScheme(unittest.TestCase):
    def setUp(self):
        super(TestScheme, self).setUp()
        options = mock.Mock()
        options.eprefix = None
        options.prefix = None

        self.options = options

    def _compute_scheme(self, bento_info, options):
        package_options = PackageOptions.from_string(bento_info)
        pkg = PackageDescription.from_string(bento_info)
        scheme = _compute_scheme(package_options)
        set_scheme_unix(scheme, options, pkg)

        return scheme


    @mock.patch("sys.platform", "linux2")
    @mock.patch("sys.version_info", (2, 4, 4, 'final', 0))
    def test_unix_scheme_default(self):
        bento_info = """\
Name: foo
"""
        self.options.prefix = self.eprefix = None

        scheme = self._compute_scheme(bento_info, self.options)
        prefix = scheme.pop("prefix")
        eprefix = scheme.pop("eprefix")
        py_version_short = scheme.pop("py_version_short")
        pkgname = scheme.pop("pkgname")

        self.assertEqual(prefix, "/usr/local")
        self.assertEqual(eprefix, "/usr/local")
        self.assertEqual(pkgname, "foo")
        self.assertEqual(py_version_short, "2.4")

        # Check that other values in scheme have not been modified
        for k, v in scheme.items():
            self.assertEqual(UNIX_REFERENCE[k], v)

    @mock.patch("sys.platform", "darwin")
    @mock.patch("sys.prefix", "/Library/Frameworks/Python.framework/Versions/2.8")
    @mock.patch("sys.exec_prefix", "/Exec/Library/Frameworks/Python.framework/Versions/2.8")
    @mock.patch("sys.version_info", (2, 4, 4, 'final', 0))
    def test_unix_scheme_default_darwin(self):
        bento_info = """\
Name: foo
"""
        self.options.prefix = self.eprefix = None

        scheme = self._compute_scheme(bento_info, self.options)
        prefix = scheme.pop("prefix")
        eprefix = scheme.pop("eprefix")
        py_version_short = scheme.pop("py_version_short")
        pkgname = scheme.pop("pkgname")

        self.assertEqual(prefix, sys.prefix)
        self.assertEqual(eprefix, sys.exec_prefix)
        self.assertEqual(pkgname, "foo")
        self.assertEqual(py_version_short, "2.4")

        # Check that other values in scheme have not been modified
        for k, v in scheme.items():
            self.assertEqual(UNIX_REFERENCE[k], v)

    @mock.patch("sys.platform", "linux2")
    @mock.patch("sys.version_info", (2, 7, 2, 'final', 0))
    def test_unix_scheme_with_prefix(self):
        bento_info = """\
Name: foo
"""
        self.options.prefix = "/home/guido"

        scheme = self._compute_scheme(bento_info, self.options)
        prefix = scheme.pop("prefix")
        eprefix = scheme.pop("eprefix")
        py_version_short = scheme.pop("py_version_short")
        pkgname = scheme.pop("pkgname")

        self.assertEqual(prefix, "/home/guido")
        self.assertEqual(eprefix, "/home/guido")
        self.assertEqual(pkgname, "foo")
        self.assertEqual(py_version_short, "2.7")

        # Check that other values in scheme have not been modified
        for k, v in scheme.items():
            self.assertEqual(UNIX_REFERENCE[k], v)

        self.options.eprefix = "/home/exec/guido"

        scheme = self._compute_scheme(bento_info, self.options)
        prefix = scheme.pop("prefix")
        eprefix = scheme.pop("eprefix")
        py_version_short = scheme.pop("py_version_short")
        pkgname = scheme.pop("pkgname")

        self.assertEqual(prefix, "/home/guido")
        self.assertEqual(eprefix, "/home/exec/guido")
        self.assertEqual(pkgname, "foo")
        self.assertEqual(py_version_short, "2.7")

        # Check that other values in scheme have not been modified
        for k, v in scheme.items():
            self.assertEqual(UNIX_REFERENCE[k], v)

    @mock.patch("sys.platform", "linux2")
    def test_unix_scheme_with_eprefix_fail(self):
        bento_info = """\
Name: foo
"""
        self.options.eprefix = "/home/guido"

        self.assertRaises(NotImplementedError, lambda: self._compute_scheme(bento_info, self.options))

    @mock.patch("sys.platform", "linux2")
    @mock.patch("sys.version_info", (2, 7, 2, 'final', 0))
    @mock.patch("distutils.command.install.INSTALL_SCHEMES", {"unix_local": MOCK_DEBIAN_SCHEME}, create=True)
    def test_unix_scheme_debian(self):
        bento_info = """\
Name: foo
"""

        scheme = self._compute_scheme(bento_info, self.options)
        prefix = scheme.pop("prefix")
        eprefix = scheme.pop("eprefix")
        sitedir = scheme.pop("sitedir")
        includedir = scheme.pop("includedir")

        self.assertEqual(prefix, "/usr/local")
        self.assertEqual(eprefix, "/usr/local")
        self.assertEqual(sitedir, "/usr/local/lib/python2.7/dist-packages")
        self.assertEqual(includedir, "/usr/local/include/python2.7/foo")

        scheme.pop("py_version_short")
        scheme.pop("pkgname")
        # Check that other values in scheme have not been modified
        for k, v in scheme.items():
            self.assertEqual(UNIX_REFERENCE[k], v)

    @mock.patch("sys.platform", "linux2")
    @mock.patch("bento.commands.configure.virtualenv_prefix", lambda: "/home/guido/.env")
    def test_unix_scheme_venv(self):
        bento_info = """\
Name: foo
"""

        scheme = self._compute_scheme(bento_info, self.options)
        prefix = scheme.pop("prefix")
        eprefix = scheme.pop("eprefix")

        self.assertEqual(prefix, "/home/guido/.env")
        self.assertEqual(eprefix, "/home/guido/.env")

        scheme.pop("py_version_short")
        scheme.pop("pkgname")
        # Check that other values in scheme have not been modified
        for k, v in scheme.items():
            self.assertEqual(UNIX_REFERENCE[k], v)
