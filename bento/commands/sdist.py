import os
import tarfile

import os.path as op

from bento.core.node_package \
    import \
        NodeRepresentation

from bento.commands.errors \
    import \
        UsageException
from bento.commands.core \
    import \
        Command, Option

import bento.compat.api as compat

def archive_basename(pkg):
    if pkg.version:
        return "%s-%s" % (pkg.name, pkg.version)
    else:
        return pkg.name

def create_tarball(node_pkg, archive_root, archive_node):
    tf = tarfile.open(archive_node.abspath(), "w:gz")
    try:
        for file in node_pkg.iter_files():
            tf.add(file, op.join(archive_root, file))
    finally:
        tf.close()

def create_zarchive(node_pkg, archive_root, archive_node):
    zid = compat.ZipFile(archive_node.abspath(), "w", compat.ZIP_DEFLATED)
    try:
        for file in node_pkg.iter_files():
            zid.write(file, op.join(archive_root, file))
    finally:
        zid.close()

_FORMATS = {"gztar": {"ext": ".tar.gz", "func": create_tarball},
            "zip": {"ext": ".zip", "func": create_zarchive}}

def create_archive(pkg, top_node, run_node, format="tgz", output_directory="dist"):
    if not format in _FORMATS:
        raise ValueError("Unknown format: %r" % (format,))

    archive_root = "%s-%s" % (pkg.name, pkg.version)
    archive_name = archive_basename(pkg) + _FORMATS[format]["ext"]
    archive_node = top_node.make_node(op.join(output_directory, archive_name))
    archive_node.parent.mkdir()

    node_pkg = NodeRepresentation(run_node, top_node)
    node_pkg.update_package(pkg)

    _FORMATS[format]["func"](node_pkg, archive_root, archive_node) 
    return archive_root, archive_node

class SdistCommand(Command):
    long_descr = """\
Purpose: create a tarball for the project
Usage:   bentomaker sdist [OPTIONS]."""
    short_descr = "create a tarball."
    common_options = Command.common_options \
                        + [Option("--output-dir",
                                  help="Output directory", default="dist"),
                           Option("--format",
                                  help="Archive format (supported: 'gztar', 'zip')", default="gztar")]
    def run(self, ctx):
        argv = ctx.get_command_arguments()
        p = ctx.options_context.parser
        o, a =  p.parse_args(argv)
        if o.help:
            p.print_help()
            return

        pkg = ctx.pkg
        format = o.format
        output_directory = o.output_dir

        # XXX: find a better way to pass archive name from other commands (used
        # by distcheck ATM)
        self.archive_root, self.archive_node = create_archive(pkg,
                ctx.top_node, ctx.run_node, o.format, o.output_dir)
