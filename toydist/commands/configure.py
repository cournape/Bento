import sys
import os

from toydist.core.utils import \
        pprint
from toydist.core.platforms import \
        get_scheme
from toydist.core import \
        PackageOptions, PackageDescription

from toydist.commands.core import \
        Command, UsageException, SCRIPT_NAME

class ConfigureState(object):
    def __init__(self):
        self.flags = {}
        self.paths = {}

    def dump(self, file='.config.bin'):
        import cPickle
        f = open(file, 'wb')
        try:
            str = cPickle.dumps(self)
            f.write(str)
        finally:
            f.close()

    @classmethod
    def from_dump(cls, file='.config.bin'):
        import cPickle
        f = open(file, 'rb')
        try:
            str = f.read()
            return cPickle.loads(str)
        finally:
            f.close()

def ensure_info_exists(opts):
    if len(opts) < 1 or opts[-1].startswith('-'):
        msg = "%s: Error: No toysetup.info found, and no toydist " \
              "configuration file given at the command line." % SCRIPT_NAME
        msg += "\nTry: %s help configure" % SCRIPT_NAME
        raise UsageException(msg)
    else:
        filename = opts[-1]
        if not os.path.exists(filename):
            msg = "%s: Error: configuration file %s not found." % \
                    (SCRIPT_NAME, filename)
            raise UsageException(msg)

    return filename

def set_scheme_options(scheme, options):
    """Set path variables given in options in scheme dictionary."""
    for k in scheme:
        if hasattr(options, k):
            val = getattr(options, k)
            if val:
                scheme[k] = val
    # XXX: define default somewhere and stick with it
    if options.prefix is not None and options.exec_prefix is None:
        scheme["eprefix"] = scheme["prefix"]

def set_flag_options(flag_opts, options):
    """Set flag variables given in options in flag dictionary."""
    # FIXME: fix this mess
    flag_vals = {}
    for k in flag_opts:
        opt_name = "with_" + k
        if hasattr(options, opt_name):
            val = getattr(options, opt_name)
            if val:
                if val == "true":
                    flag_vals[k] = True
                elif val == "false":
                    flag_vals[k] = False
                else:
                    msg = """Error: %s: option %s expects a true or false argument"""
                    raise UsageException(msg % (SCRIPT_NAME, "--with-%s" % k))

    return flag_vals

class ConfigureCommand(Command):
    long_descr = """\
Purpose: configure the project
Usage: toymaker configure [OPTIONS] [package description file]."""
    short_descr = "configure the project."
    def run(self, opts):

        # We need to obtain the package description ASAP, as we need to parse
        # it to get the options (i.e. we cannot use the option handling mechanism).
        candidate = "toysetup.info"
        if len(opts) < 1 or opts[-1].startswith('-'):
            pass
        else:
            candidate = opts[-1]

        if os.path.exists(candidate):
            filename = candidate
        else:
            filename = ensure_info_exists(opts)

        # As the configure command line handling is customized from
        # the toysetup.info (flags, paths variables), we cannot just
        # call set_options_parser.
        pkg_opts = PackageOptions.from_file(filename)
        scheme, flag_opts = self.add_configuration_options(pkg_opts)

        self.set_option_parser()
        o, a = self.parser.parse_args(opts)
        if o.help:
            self.parser.print_help()
            return

        set_scheme_options(scheme, o)
        flag_vals = set_flag_options(flag_opts, o)

        # Cache the built package description to avoid reparsing it for
        # subsequent commands
        pkg = PackageDescription.from_file(filename, flag_vals)

        s = ConfigureState()
        s.paths = scheme
        s.flags = flag_vals
        s.package_description = filename
        s.pkg = pkg
        s.dump()
        pprint('GREEN', "Writing configuration state in file %s" % '.config.bin')

    def add_configuration_options(self, pkg_opts):
        """Add the path and flags-related options as defined in the
        toysetup.info file to the command."""
        scheme, scheme_opts = get_scheme(sys.platform)
        # XXX: abstract away those, as it is copied from distutils
        py_version = sys.version.split()[0]
        scheme['py_version_short'] = py_version[0:3]

        scheme['pkgname'] = pkg_opts.name

        # Add path options to the path scheme
        for name, f in pkg_opts.path_options.items():
            scheme[name] = f.default_value
            scheme_opts[name] = {'opts': ['--%s' % f.name],
                                 'help': '%s [%s]' % (f.description, f.default_value)}

        for name, opt in scheme_opts.items():
            self.opts.append(opt)

        flag_opts = {}
        for name, v in pkg_opts.flag_options.items():
            flag_opts[name] = {
                    "opts": ["--with-%s" % v.name],
                    "help": "%s [default=%s]" % (v.description, v.default_value)}
            self.opts.append(flag_opts[name])

        return scheme, flag_opts
