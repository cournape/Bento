import base64
import sys

import os.path as op

from bento.pypi.register_utils \
    import \
        encode_multipart, _BOUNDARY
from bento.conv \
    import \
        pkg_to_distutils_meta_pkg_info
from bento.utils.utils \
    import \
        extract_exception
from bento.errors \
    import \
        PyPIError, InvalidRepository

from six \
    import \
        PY3

import six

try:
    from hashlib import md5
except ImportError:
    from md5 import md5




if PY3:
    from urllib.request \
        import \
            Request, HTTPBasicAuthHandler, HTTPError, URLError, urlparse, urlopen
else:
    from urllib2 \
        import \
            Request, HTTPBasicAuthHandler, HTTPError, URLError, urlopen
    from urlparse \
        import \
            urlparse

def build_upload_post_data(filename, dist_type, package, sign=False, comment=""):
    pyversion = ".".join(str(i) for i in sys.version_info[:2])

    f = open(filename,'rb')
    try:
        content = f.read()
    finally:
        f.close()

    data = pkg_to_distutils_meta_pkg_info(package)
    data[":action"] = "file_upload"
    data["protocol_version"] = "1"
    data.update({
        # file content
        'content': (op.basename(filename), content),
        'filetype': dist_type,
        'pyversion': pyversion,
        'md5_digest': md5(content).hexdigest(),

        # additional meta-data
        'metadata_version' : '1.0',

        'comment': comment,
    })

    if sign:
        raise NotImplementedError("Signing not yet implemented.")
        data['gpg_signature'] = (op.basename(filename) + ".asc",
                                 open(filename+".asc").read())

    return data

def build_request(repository, post_data, auth):
    files = []
    for key in ('content', 'gpg_signature'):
        if key in post_data:
            filename_, value = post_data.pop(key)
            files.append((key, filename_, value))
    content_type, body = encode_multipart(post_data.items(), files)

    headers = {'Content-type': content_type,
               'Content-length': str(len(body)),
               'Authorization': auth}

    return Request(repository, data=body, headers=headers)

def upload(dist_filename, dist_type, package, config, sign=False):
    schema, netloc, url, params, query, fragments = urlparse(config.repository)
    if params or query or fragments:
        raise InvalidRepository("Incompatible url %s" % config.repository)

    if schema not in ('http', 'https'):
        raise InvalidRepository("unsupported schema " + schema)

    if sign:
        raise NotImplementedError()

    data = build_upload_post_data(dist_filename, dist_type, package)
    userpass = (config.username + ":" + config.password).encode("ascii")
    auth = six.b("Basic ") + base64.standard_b64encode(userpass)
    request = build_request(config.repository, data, auth)

    try:
        result = urlopen(request)
        status = result.getcode()
        reason = result.msg
    except HTTPError:
        e = extract_exception()
        status = e.code
        reason = e.msg
    except URLError:
        e = extract_exception()
        reason = e.reason
        raise PyPIError(
                "Could not upload to repository %r - error %s" \
                % (config.repository, reason))

    if status != 200:
        raise PyPIError(
                "Could not upload to repository %r - error %s (server answered '%s')" \
                % (config.repository, status, reason))
