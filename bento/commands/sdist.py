import os
import tarfile

from bento.core.package import \
        PackageDescription, file_list

from bento.commands.errors \
    import \
        UsageException
from bento.commands.core import \
    Command
from bento.core.utils \
    import \
        ensure_dir
from bento._config import \
    BENTO_SCRIPT

def tarball_basename(dist_name, version=None):
    if version:
        return "%s-%s" % (dist_name, version)
    else:
        return dist_name

class SdistCommand(Command):
    long_descr = """\
Purpose: create a tarball for the project
Usage:   bentomaker sdist [OPTIONS]."""
    short_descr = "create a tarball."
    def __init__(self):
        Command.__init__(self)
        self.tarname = None
        self.topdir = None

    def run(self, ctx):
        argv = ctx.get_command_arguments()
        p = ctx.options_context.parser
        o, a =  p.parse_args(argv)
        if o.help:
            p.print_help()
            return

        filename = BENTO_SCRIPT
        if not len(a) > 0:
            if not os.path.exists(filename):
                raise UsageException("Missing %s file" % BENTO_SCRIPT)

        pkg = PackageDescription.from_file(filename)
        tarname = tarball_basename(pkg.name, pkg.version) + ".tar.gz"
        self.tarname = os.path.abspath(os.path.join("dist", tarname))
        self.topdir = "%s-%s" % (pkg.name, pkg.version)
        create_tarball(pkg, ctx.top_node, self.tarname, self.topdir)

def create_tarball(pkg, top_node, tarname=None, topdir=None):
    if tarname is None:
        basename = tarball_basename(pkg.name, pkg.version)
        tarname = "%s.tar.gz" % basename
    if topdir is None:
        topdir = "%s-%s" % (pkg.name, pkg.version)

    ensure_dir(tarname)
    tf = tarfile.open(tarname, "w:gz")
    try:
        for file in file_list(pkg, top_node):
            tf.add(file, os.path.join(topdir, file))
    finally:
        tf.close()
    return tarname
