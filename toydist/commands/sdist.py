import os
import tarfile

from toydist.core.utils import \
        pprint
from toydist.core.package import \
        PackageDescription, file_list

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

        pkg = PackageDescription.from_file(filename)

        basename = tarball_basename(pkg.name, pkg.version)
        topname = "%s-%s" % (pkg.name, pkg.version)
        tarname = "%s.tar.gz" % basename

        tf = tarfile.open(tarname, "w:gz")
        try:
            for file in file_list(pkg):
                tf.add(file, os.path.join(topname, file))
        finally:
            tf.close()
