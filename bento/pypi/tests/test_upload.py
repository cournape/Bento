import os
import shutil
import tempfile
import urllib2

import os.path as op

import mock

import bento.errors
import six

from bento.core.package \
    import \
        PackageDescription
from bento.pypi.register_utils \
    import \
        PyPIConfig
from bento.pypi.upload_utils \
    import \
        build_upload_post_data, build_request, upload

from bento.compat.api import moves

# FIXME: there has to be a simpler way to do this
class MockedResult(object):
    def __init__(self, code, msg):
        self._code = code
        self.msg = msg

    def getcode(self):
        return self._code

#def raise_error_factory(url=None, code=200, msg=""):
#    if url is None:
#        url = "http://example.com"
#    def f(request):
#        raise urllib2.HTTPError(url, code, msg, {}, six.moves.StringIO())
#    return f

def my_urlopen_factory(exception):
    def my_urlopen(request):
        raise exception
    return my_urlopen

class TestUpload(moves.unittest.TestCase):
    def setUp(self):
        self.package = PackageDescription.from_string("""\
Name: foo
""")
        self.cwd = tempfile.mkdtemp()
        try:
            self.old_cwd = os.getcwd()
            os.chdir(self.cwd)

            filename = op.join(self.cwd, "foo.bin")
            fp = open(filename, "wb")
            try:
                fp.write("garbage")
            finally:
                fp.close()

        except:
            shutil.rmtree(self.cwd)

    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.cwd)

    def test_upload_post_data(self):
        post_data = build_upload_post_data("foo.bin", "bdist_dumb", self.package)
        self.assertEqual(post_data[":action"], "file_upload")
        self.assertEqual(post_data["content"], ("foo.bin", "garbage"))

    def test_signing(self):
        self.assertRaises(NotImplementedError, build_upload_post_data, "foo.bin", "bdist_dumb", self.package, True)

    def test_build_request(self):
        repository = "http://localhost"
        post_data = build_upload_post_data("foo.bin", "bdist_dumb", self.package)
        request = build_request(repository, post_data, "dummy_auth")
        r_headers = {
                "Content-type": "multipart/form-data; boundary=--------------GHSKFJDLGDS7543FJKLFHRE75642756743254",
                "Content-length": "2238",
                "Authorization": "dummy_auth"}
        self.assertEqual(request.headers, r_headers)

    @mock.patch("urllib2.urlopen", lambda request: MockedResult(200, ""))
    def test_upload(self):
        config = PyPIConfig("john", "password", repository="http://localhost")
        upload("foo.bin", "bdist_dumb", self.package, config)

    @mock.patch("urllib2.urlopen", my_urlopen_factory(
        urllib2.HTTPError("", 404, "url not found", {}, six.moves.StringIO())))
    def test_upload_error_404(self):
        config = PyPIConfig("john", "password", repository="http://localhost")
        self.assertRaises(bento.errors.PyPIError, upload, "foo.bin", "bdist_dumb", self.package, config)

    @mock.patch("urllib2.urlopen", my_urlopen_factory(urllib2.URLError("dummy")))
    def test_upload_error_no_host(self):
        config = PyPIConfig("john", "password", repository="http://llocalhost")
        self.assertRaises(urllib2.URLError, upload, "foo.bin", "bdist_dumb", self.package, config)

    @mock.patch("urllib2.urlopen", lambda request: MockedResult(200, ""))
    def test_upload_auth(self):
        config = PyPIConfig("john", "password", repository="http://localhost")
        self.assertRaises(NotImplementedError, upload, "foo.bin", "bdist_dumb", self.package, config, True)
