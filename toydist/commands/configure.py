import sys
import os

from toydist.cabal_parser.cabal_parser import \
        parse, ParseError
from toydist.utils import \
        subst_vars, pprint
from toydist.core.platforms import \
        get_scheme

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

class ConfigureCommand(Command):
    long_descr = """\
Purpose: configure the project
Usage: toymaker configure [OPTIONS] [package description file]."""
    short_descr = "configure the project."
    def run(self, opts):

        # We need to obtain the package description ASAP, as we need to parse
        # it to get the options (i.e. we cannot use the option handling mechanism).
        if os.path.exists('toysetup.info'):
            filename = 'toysetup.info'
        else:
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

        f = open(filename, 'r')
        try:
            data = f.readlines()
            try:
                d = parse(data)
            except ParseError, e:
                msg = "Error while parsing file %s\n" % filename
                e.args = (msg,) +  e.args
                raise e

            try:
                path_options = d['path_options']
            except KeyError:
                path_options = {}

            try:
                flag_options = d['flag_options']
            except KeyError:
                flag_options = {}

            pkg_name = d['name']
        finally:
            f.close()

        scheme, scheme_opts = get_scheme(sys.platform)
        # XXX: abstract away those, as it is copied from distutils
        py_version = sys.version.split()[0]
        scheme['py_version_short'] = py_version[0:3]

        scheme['pkgname'] = d["name"]

        # Add path options to the path scheme
        for name, f in path_options.items():
            scheme[name] = f.default_value
            scheme_opts[name] = {'opts': ['--%s' % f.name],
                                 'help': '%s [%s]' % (f.description, f.default_value)}

        for name, opt in scheme_opts.items():
            self.opts.append(opt)

        self.set_option_parser()
        o, a = self.parser.parse_args(opts)
        if o.help:
            self.parser.print_help()
            return

        for k in scheme:
            if hasattr(o, k):
                val = getattr(o, k)
                if val:
                    scheme[k] = val

        s = ConfigureState()
        s.paths = scheme
        s.package_description = filename
        s.dump()
        pprint('GREEN', "Writing configuration state in file %s" % '.config.bin')
