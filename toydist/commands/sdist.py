import os
import tarfile

from toydist.utils import \
        pprint, expand_glob, find_package
from toydist.cabal_parser.cabal_parser import \
        parse

from toydist.commands.core import \
    Command, UsageException

def tarball_basename(dist_name, version=None):
    if version:
        return "%s-%s" % (dist_name, version)
    else:
        return dist_name

class SdistCommand(Command):
    long_descr = """\
Purpose: create a tarball for the project
Usage:   toymaker sdist [OPTIONS]."""
    short_descr = "create a tarball."
    def run(self, opts):
        self.set_option_parser()
        o, a = self.parser.parse_args(opts)
        if o.help:
            self.parser.print_help()
            return

        filename = "toysetup.info"
        if not len(a) > 0:
            if not os.path.exists(filename):
                raise UsageException("Missing %s file" % "toysetup.info")

        info_file = open(filename, 'r')
        try:
            data = info_file.readlines()
            d = parse(data)

            sourcefiles = []

            basename = tarball_basename(d['name'], d['version'])
            topname = "%s-%s" % (d['name'], d['version'])
            tarname = "%s.tar.gz" % basename

            tf = tarfile.open(tarname, "w:gz")
            try:
                for name in d["extrasourcefiles"]:
                    tf.add(name, os.path.join(topname, name))
                library = d["library"][""]

                python_files = []
                # FIXME: root_src
                root_src = ""
                if library.has_key('packages'):
                    for p in library['packages']:
                        python_files.extend(find_package(p, root_src))
                if library.has_key('modules'):
                    for m in library['modules']:
                        python_files.append(os.path.join(root_src, '%s.py' % m))

                for p in python_files:
                    tf.add(p, os.path.join(topname, p))

                data_files =[]
                if d.has_key('datafiles'):
                    sections = d['datafiles']
                    for section in sections.values():
                        srcdir = section['srcdir']
                        files = section['files']
                        data_files.extend([os.path.join(srcdir, f) for f in files])

                for p in data_files:
                    tf.add(p, os.path.join(topname, p))

            finally:
                tf.close()

        finally:
            info_file.close()
