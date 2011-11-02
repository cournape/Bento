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
        for filename, alias in node_pkg.iter_source_files():
            tf.add(filename, op.join(archive_root, alias))
    finally:
        tf.close()

def create_zarchive(node_pkg, archive_root, archive_node):
    zid = compat.ZipFile(archive_node.abspath(), "w", compat.ZIP_DEFLATED)
    try:
        for filename, alias in node_pkg.iter_source_files():
            zid.write(filename, op.join(archive_root, alias))
    finally:
        zid.close()

_FORMATS = {"gztar": {"ext": ".tar.gz", "func": create_tarball},
            "zip": {"ext": ".zip", "func": create_zarchive}}

def create_archive(archive_name, archive_root, node_pkg, top_node, run_node, format="tgz", output_directory="dist"):
    if not format in _FORMATS:
        raise ValueError("Unknown format: %r" % (format,))

    archive_node = top_node.make_node(op.join(output_directory, archive_name))
    archive_node.parent.mkdir()

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
                                  help="Archive format (supported: 'gztar', 'zip')", default="gztar"),
                           Option("--output-file",
                                  help="Archive filename (default: $pkgname-$version.$archive_extension)")]

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

        archive_root = "%s-%s" % (pkg.name, pkg.version)
        if not o.output_file:
            archive_name = archive_basename(pkg) + _FORMATS[format]["ext"]
        else:
            output = op.basename(o.output_file)
            if output != o.output_file:
                raise BentoError("Invalid output file: should not contain any directory")
            archive_name = output

        # XXX: find a better way to pass archive name from other commands (used
        # by distcheck ATM)
        self.archive_root, self.archive_node = create_archive(archive_name, archive_root, ctx._node_pkg,
                ctx.top_node, ctx.run_node, o.format, o.output_dir)
