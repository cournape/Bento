from bento.commands.core \
    import \
        Command, Option
from bento.commands.register \
    import \
        _read_pypirc
from bento.pypi.register_utils \
    import \
        DEFAULT_REPOSITORY, PyPIConfig
from bento.pypi.upload_utils \
    import \
        upload

import bento.errors

_SUPPORTED_DISTRIBUTIONS = {"source": "sdist", "egg": "bdist_egg"}

class UploadPyPI(Command):
    long_descr = """\
Purpose: register the package to pypi
Usage: bentomaker register [OPTIONS] distribution_file"""
    short_descr = "register packages to pypi."
    common_options = Command.common_options \
                        + [Option("-r", "--repository",
                                  help="Repository to use in .pypirc"),
                           Option("-u", "--username",
                                  help="Username to use for registration"),
                           Option("-p", "--password",
                                  help="Password to use for registration"),
                           Option("--repository-url",
                                  help="Repository URL to use for registration"),
                           Option("-t", "--distribution-type",
                                  help="Force distribution type (sdist, bdist_wininst, etc...)"),
                                  ]
    def run(self, context):
        o, a = context.get_parsed_arguments()
        if len(a) < 1:
            context.options_context.parser.print_usage()
            # FIXME
            raise NotImplementedError("expected file argument")
        else:
            filename = a[0]

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

        if o.distribution_type is None:
            # FIXME
            raise NotImplementedError("automatic distribution type not yet implemented")
        if not o.distribution_type in _SUPPORTED_DISTRIBUTIONS:
            # FIXME
            raise NotImplementedError()

        upload_type = _SUPPORTED_DISTRIBUTIONS[o.distribution_type]
        upload(filename, upload_type, context.pkg, config=config)
