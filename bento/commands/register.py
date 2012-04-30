import urllib2
import urlparse

import os.path as op

import bento.errors

from bento.commands.core \
    import \
        Command, Option
from bento.pypi.register_utils \
    import \
        build_post_data, post_to_server, DEFAULT_REPOSITORY, read_pypirc, PyPIConfig

def _read_pypirc(repository):
    filename = op.join(op.expanduser("~"), ".pypirc")
    if not op.exists(filename):
        raise bento.errors.UsageException(
                "file %r not found (automatic creation of .pypirc not supported yet" % filename)
    try:
        return read_pypirc(repository)
    except bento.errors.InvalidPyPIConfig:
        raise bento.errors.UsageException("repository %r not found in %r" % (repository, filename))

class RegisterPyPI(Command):
    long_descr = """\
Purpose: register the package to pypi
Usage: bentomaker register [OPTIONS]"""
    short_descr = "register packages to pypi."
    common_options = Command.common_options \
                        + [Option("-r", "--repository",
                                  help="Repository to use in .pypirc"),
                           Option("-u", "--username",
                                  help="Username to use for registration"),
                           Option("-p", "--password",
                                  help="Password to use for registration"),
                           Option( "--repository-url",
                                  help="Repository URL to use for registration"),
                                  ]
    def run(self, context):
        o, a = context.get_parsed_arguments()
        if o.repository and (o.username or o.password or o.repository_url):
            raise bento.errors.UsageException(
                    "Cannot specify repository and username/password/url at the same time")
        if not (o.repository or (o.username or o.password or o.repository_url)):
            # FIXME: why does distutils use DEFAULT_REPOSITORY (i.e. an url)
            # here ?
            config = _read_pypirc(DEFAULT_REPOSITORY)
        elif o.repository:
            config = _read_pypirc(o.repository)
        else:
            config = PyPIConfig(o.username, o.password, o.repository_url)

        auth = urllib2.HTTPPasswordMgr()
        host = urlparse.urlparse(config.repository)[0]
        auth.add_password(config.realm, host, config.username, config.password)

        post_data = build_post_data(context.pkg, "submit")
        code, msg = post_to_server(post_data, config)
        if code != 200:
            raise bento.errors.BentoError("Error while submitting package metadata to server: %r" % msg)
