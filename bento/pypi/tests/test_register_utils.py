import os
import shutil
import tempfile

import os.path as op

from six.moves \
    import \
        StringIO

import mock

from bento.pypi.register_utils \
    import \
        build_post_data, encode_multipart, post_to_server, DEFAULT_REALM, \
        PyPIConfig, parse_pypirc
from bento.compat.api.moves \
    import \
        unittest
from bento.core \
    import \
        PackageDescription

from six \
    import \
        PY3

import six

if PY3:
    from urllib.request \
        import \
            HTTPPasswordMgr, urlparse, HTTPError, URLError
    _OPENER_DIRECTOR = "urllib.request.OpenerDirector"
else:
    from urllib2 \
        import \
            Request, HTTPPasswordMgr, HTTPError, URLError
    from urlparse \
        import \
            urlparse
    _OPENER_DIRECTOR = "urllib2.OpenerDirector"

class TestRegisterUtils(unittest.TestCase):
    def test_build_post_data(self):
        r_content = six.b("""----------------GHSKFJDLGDS7543FJKLFHRE75642756743254\r\n""" \
"""Content-Disposition: form-data; name="maintainer"\r\n\r\n\r\n""" \
"""----------------GHSKFJDLGDS7543FJKLFHRE75642756743254\r\n""" \
"""Content-Disposition: form-data; name="name"\r\n\r\n""" \
"""foo\r\n""" \
"""----------------GHSKFJDLGDS7543FJKLFHRE75642756743254\r\n""" \
"""Content-Disposition: form-data; name="license"\r\n\r\n\r\n""" \
"""----------------GHSKFJDLGDS7543FJKLFHRE75642756743254\r\n""" \
"""Content-Disposition: form-data; name="author"\r\n\r\n""" \
"""John Doe\r\n""" \
"""----------------GHSKFJDLGDS7543FJKLFHRE75642756743254\r\n""" \
"""Content-Disposition: form-data; name="url"\r\n\r\n\r\n""" \
"""----------------GHSKFJDLGDS7543FJKLFHRE75642756743254\r\n""" \
"""Content-Disposition: form-data; name=":action"\r\n\r\n""" \
"""submit\r\n""" \
"""----------------GHSKFJDLGDS7543FJKLFHRE75642756743254\r\n""" \
"""Content-Disposition: form-data; name="download_url"\r\n\r\n\r\n""" \
"""----------------GHSKFJDLGDS7543FJKLFHRE75642756743254\r\n""" \
"""Content-Disposition: form-data; name="maintainer_email"\r\n\r\n\r\n""" \
"""----------------GHSKFJDLGDS7543FJKLFHRE75642756743254\r\n""" \
"""Content-Disposition: form-data; name="author_email"\r\n\r\n\r\n""" \
"""----------------GHSKFJDLGDS7543FJKLFHRE75642756743254\r\n""" \
"""Content-Disposition: form-data; name="version"\r\n\r\n""" \
"""1.0\r\n""" \
"""----------------GHSKFJDLGDS7543FJKLFHRE75642756743254\r\n""" \
"""Content-Disposition: form-data; name="long_description"\r\n\r\n\r\n""" \
"""----------------GHSKFJDLGDS7543FJKLFHRE75642756743254\r\n""" \
"""Content-Disposition: form-data; name="description"\r\n\r\n\r\n""" \
"""----------------GHSKFJDLGDS7543FJKLFHRE75642756743254--\r\n""" \
"""""")
        bento_info = """\
Name: foo
Version: 1.0
Author: John Doe
"""
        package = PackageDescription.from_string(bento_info)
        post_data = build_post_data(package, "submit")
        content_type, body = encode_multipart(post_data.items(), [])
        self.assertEqual(r_content, body)

    @mock.patch(_OPENER_DIRECTOR, mock.MagicMock())
    def test_register_server(self):
        package = PackageDescription(name="foo")
        repository = 'http://testpypi.python.org/pypi'
        realm = DEFAULT_REALM
        config = PyPIConfig(username="cdavid", password="yoyo", repository=repository, realm=realm)

        auth = HTTPPasswordMgr()
        host = urlparse(config.repository)[0]
        auth.add_password(config.realm, host, config.username, config.password)

        post_data = build_post_data(package, "submit")
        code, msg = post_to_server(post_data, config, auth)
        self.assertEqual(code, 200)
        self.assertEqual(msg, "OK")

    @mock.patch("%s.open" % _OPENER_DIRECTOR,
                mock.MagicMock(side_effect=HTTPError("", 404, "", {}, None)))
    def test_register_server_http_errors(self):
        code, msg = self._test_register_server_errors()
        self.assertEqual(code, 404)
        self.assertEqual(msg, "")

    @mock.patch("%s.open" % _OPENER_DIRECTOR,
                mock.MagicMock(side_effect=URLError("")))
    def test_register_server_url_errors(self):
        code, msg = self._test_register_server_errors()
        self.assertEqual(code, 500)

    def _test_register_server_errors(self):
        package = PackageDescription(name="foo")
        config = PyPIConfig.from_string("""
[distutils]
index-servers = pypi

[pypi]
username = cdavid
password = yoyo
server = http://testpypi.python.org
""")

        post_data = build_post_data(package, "submit")
        return post_to_server(post_data, config)

class TestReadPyPI(unittest.TestCase):
    def test_pypi_config(self):
        data = """\
[distutils]
index-servers =
    test

[test]
username:cdavid
password:yoyo
repository:http://testpypi.python.org
"""
        config = PyPIConfig.from_file(StringIO(data), repository="test")
        self.assertEqual(config.username, "cdavid")
        self.assertEqual(config.password, "yoyo")

    def test_new_format_default(self):
        data = """\
[distutils]
index-servers =

[pypi]
username:cdavid
password:yoyo
repository:http://testpypi.python.org
"""
        config = parse_pypirc(StringIO(data), 'pypi')
        self.assertEqual(config.username, "cdavid")
        self.assertEqual(config.password, "yoyo")
        self.assertEqual(config.repository, "http://testpypi.python.org")

    def test_invalid_format(self):
        self.assertRaises(ValueError, parse_pypirc, StringIO(""))

    def test_new_format(self):
        data = """\
[distutils]
index-servers =
    test
    pypi

[test]
username:cdavid
password:yoyo
repository:http://testpypi.python.org

[pypi]
username:david
password:yeye
repository:http://pypi.python.org
"""
        config = parse_pypirc(StringIO(data), "pypi")
        self.assertEqual(config.username, "david")
        self.assertEqual(config.password, "yeye")

        config = parse_pypirc(StringIO(data), repository="test")
        self.assertEqual(config.username, "cdavid")
        self.assertEqual(config.password, "yoyo")
        self.assertEqual(config.repository, "http://testpypi.python.org")

    def test_old_format(self):
        data = """\
[server-login]
username:cdavid
password:yoyo
repository:http://testpypi.python.org
"""
        config = parse_pypirc(StringIO(data))
        self.assertEqual(config.username, "cdavid")
        self.assertEqual(config.password, "yoyo")
        self.assertEqual(config.repository, "http://testpypi.python.org")

class TestReadPyPIDefault(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        try:
            self.p = mock.patch("os.path.expanduser", lambda x: self.d)
            self.p.start()
        except:
            shutil.rmtree(self.d)
            raise

    def tearDown(self):
        self.p.stop()
        shutil.rmtree(self.d)

    def test_read_pypirc(self):
        # Guard to make sure we don't write an actual file by mistake
        try:
            fp = open(op.join(op.expanduser("~"), ".pypirc"), "rt")
            fp.close()
            raise ValueError()
        except IOError:
            pass

        fp = open(op.join(op.expanduser("~"), ".pypirc"), "wt")
        try:
            fp.write("")
        finally:
            fp.close()
