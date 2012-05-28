import os.path as op

from bento.conv \
    import \
        pkg_to_distutils_meta
from bento.utils.utils \
    import \
        extract_exception
from bento.errors \
    import \
        InvalidPyPIConfig

from six.moves \
    import \
        configparser, StringIO
from six \
    import \
        PY3

import six

if PY3:
    from urllib.request \
        import \
            Request, HTTPBasicAuthHandler, HTTPError, URLError, build_opener
else:
    from urllib2 \
        import \
            Request, HTTPBasicAuthHandler, HTTPError, URLError, build_opener

DEFAULT_REPOSITORY = 'http://pypi.python.org/pypi'
DEFAULT_REALM = 'pypi'

REALM = DEFAULT_REALM
REPOSITORY = 'http://testpypi.python.org/pypi'

_BOUNDARY = six.b('--------------GHSKFJDLGDS7543FJKLFHRE75642756743254')

def _read_new_format(config, repository):
    sections = config.sections()

    # let's get the list of servers
    index_servers = config.get('distutils', 'index-servers')
    _servers = [server.strip() for server in
                index_servers.split('\n')
                if server.strip() != '']
    if _servers == []:
        # nothing set, let's try to get the default pypi
        if 'pypi' in sections:
            _servers = ['pypi']
        else:
            # the file is not properly defined
            raise InvalidPyPIConfig("No index-servers section or pypi section")
    for server in _servers:
        current = PyPIConfig()
        current.username = config.get(server, 'username')
        current.server = server

        # optional params
        def _get_default(key, default):
            if config.has_option(server, key):
                return config.get(server, key)
            else:
                return default

        current.repository = _get_default("repository", DEFAULT_REPOSITORY)
        current.realm = _get_default("realm", DEFAULT_REALM)
        current.password = _get_default("password", None)

        if (current.server == repository or current.repository == repository):
            return current
    raise InvalidPyPIConfig("No section for repository %r found" % repository)

def _read_old_format(config):
    server = 'server-login'
    if config.has_option(server, 'repository'):
        repository = config.get(server, 'repository')
    else:
        repository = DEFAULT_REPOSITORY

    return PyPIConfig(username=config.get(server, 'username'),
            password=config.get(server, 'password'),
            repository=repository,
            server=server,
            realm=DEFAULT_REALM)

def read_pypirc(repository=DEFAULT_REPOSITORY):
    """Read the default .pypirc file.

    Returns a PyPIConfig instance if the default .pypirc can be found. Raises
    an IOError otherwise

    Parameters
    ----------
    repository: str
        repository to use
    """
    rc = op.join(op.expanduser('~'), '.pypirc')
    if op.exists(rc):
        fp = open(rc, "rt")
        try:
            return parse_pypirc(fp, repository)
        finally:
            fp.close()
    else:
        return IOError("Default pypirc config file not found: %r" % rc)

def parse_pypirc(fp, repository=DEFAULT_REPOSITORY):
    """Parse the given pypi config file.

    Returns a PyPIConfig instance if the file can be parsed.

    Parameters
    ----------
    fp: file-like object
        contains the content of the config file
    repository: str
        repository to look for
    """
    config = configparser.RawConfigParser()
    config.readfp(fp)
    sections = config.sections()
    if 'distutils' in sections:
        return _read_new_format(config, repository)
    elif 'server-login' in sections:
        return _read_old_format(config)
    else:
        msg = "Unrecognized format"
        if hasattr(fp, "name"):
            msg += " (for file %r)" % fp.name
        raise ValueError(msg)

class PyPIConfig(object):
    @classmethod
    def from_file(cls, fp=None, repository=DEFAULT_REPOSITORY):
        """Create a PyPIConfig instance from the give file for the give repository.

        Parameters
        ----------
        fp: file-like object or None
            If None, attemps to read the .pypirc file. Otherwise, must be a
            file-like object
        repository: str
            Repository to consider in the .pypirc file.
        """
        if fp is None:
            return read_pypirc(repository)
        else:
            return parse_pypirc(fp, repository)

    @classmethod
    def from_string(cls, s, repository=DEFAULT_REPOSITORY):
        return cls.from_file(StringIO(s), repository)

    def __init__(self, username=None, password=None, repository=None,
            server=None, realm=None):
        self.username = username
        self.password = password
        self.repository = repository
        self.realm = realm
        self.server = server

def encode_multipart(fields, files, boundary=None):
    """Prepare a multipart HTTP request.

    *fields* is a sequence of (name: str, value: str) elements for regular
    form fields, *files* is a sequence of (name: str, filename: str, value:
    bytes) elements for data to be uploaded as files.

    Returns (content_type: bytes, body: bytes) ready for httplib.HTTP.
    """
    # Taken from http://code.activestate.com/recipes/146306

    if boundary is None:
        boundary = _BOUNDARY
    elif not isinstance(boundary, str):
        raise TypeError('boundary must be str, not %r' % type(boundary))

    l = []
    for key, values in fields:
        # handle multiple entries for the same name
        if not isinstance(values, (tuple, list)):
            values = [values]

        for value in values:
            l.extend((
                six.b('--') + boundary,
                # XXX should encode to match packaging but it causes bugs
                ('Content-Disposition: form-data; name="%s"' % key).encode("utf-8"),
                six.b(''),
                value.encode("utf-8")))

    for key, filename, value in files:
        l.extend((
            six.b('--') + boundary,
            ('Content-Disposition: form-data; name="%s"; filename="%s"' %
             (key, filename)).encode("utf-8"),
            six.b(''),
            value))

    l.append(six.b('--') + boundary + six.b('--'))
    l.append(six.b(''))

    body = six.b('\r\n').join(l)
    content_type = six.b('multipart/form-data; boundary=') + boundary
    return content_type, body

def build_post_data(pkg, action):
    data = pkg_to_distutils_meta(pkg)
    data[":action"] = action
    return data

def post_to_server(post_data, config, auth=None):
    """Send the given post_data to the pypi server.

    Parameters
    ----------
    post_data: dict
        Usually the dict returned by build_post_data
    config: object
        A PyPIConfig instance
    auth: object or None
        HTTP authentification object.

    Returns
    -------
    code: int
        HTTP status code
    msg: str
        Message received back from the server
    """
    content_type, body = encode_multipart(post_data.items(), [])

    # build the Request
    headers = {
        'Content-type': content_type,
        'Content-length': str(len(body))
    }
    req = Request(config.repository, body, headers)

    # handle HTTP and include the Basic Auth handler
    opener = build_opener(HTTPBasicAuthHandler(password_mgr=auth))
    try:
        opener.open(req)
    except HTTPError:
        e = extract_exception()
        code, msg = e.code, e.msg
    except URLError:
        e = extract_exception()
        code, msg = 500, str(e)
    else:
        code, msg = 200, 'OK'

    return code, msg
