import sys
import os

from toydist.cabal_parser.cabal_parser import \
        parse
from toydist.utils import \
        subst_vars
from toydist.sysconfig import \
        get_scheme

from toydist.commands.core import \
        Command, UsageException, SCRIPT_NAME

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
            d = parse(data)
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

        scheme, scheme_opts = get_scheme(sys.platform, pkg_name)
        # XXX: abstract away those, as it is copied from distutils
        py_version = sys.version.split()[0]
        scheme['py_version_short'] = py_version[0:3]

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

        for k in scheme:
            print '%s: %s' % (k, subst_vars(scheme[k], scheme))

