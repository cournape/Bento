import os
import sys
import zipfile

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from toydist.private.bytecode import \
        compile
from toydist.core.utils import \
        pprint
from toydist.core import \
        PackageMetadata
from toydist.conv import \
        to_distutils_meta
from toydist.installed_package_description import \
        InstalledPkgDescription

from toydist.commands.core import \
        Command, SCRIPT_NAME, UsageException

def egg_filename(fullname, pyver=None):
    if not pyver:
        pyver = ".".join([str(i) for i in sys.version_info[:2]])
    return "%s-py%s.egg" % (fullname, pyver)

class BuildEggCommand(Command):
    long_descr = """\
Purpose: build egg
Usage:   toymaker build_egg [OPTIONS]"""
    short_descr = "build egg."

    def run(self, opts):
        self.set_option_parser()
        o, a = self.parser.parse_args(opts)
        if o.help:
            self.parser.print_help()
            return

        filename = "installed-pkg-info"
        if not os.path.exists(filename):
            raise UsageException("%s: error: %s subcommand require executed build" \
                    % (SCRIPT_NAME, "build_egg"))

        ipkg = InstalledPkgDescription.from_file(filename)
        meta = PackageMetadata.from_installed_pkg_description(ipkg)

        # FIXME: fix egg name
        egg = egg_filename(os.path.join("toydist", meta.fullname))
        egg_dir = os.path.dirname(egg)
        if egg_dir:
            if not os.path.exists(egg_dir):
                os.makedirs(egg_dir)

        zid = zipfile.ZipFile(egg, "w")
        try:
            ret = write_egg_info(ipkg)
            try:
                for k, v in ret.items():
                    v.seek(0)
                    zid.writestr(os.path.join("EGG-INFO", k), v.getvalue())
            finally:
                for v in ret.values():
                    v.close()

            ipkg.path_variables["sitedir"] = "."
            file_sections = ipkg.resolve_paths()
            for type in file_sections:
                for value in file_sections[type].values():
                    for f in value:
                        zid.write(f[0], f[1])

            pprint("PINK", "Byte-compiling ...")
            for section in file_sections["pythonfiles"].values():
                for source, target in section:
                    zid.writestr("%sc" % target, compile(source))
        finally:
            zid.close()

        return 

def write_egg_info(ipkg):
    ret = {}

    meta = PackageMetadata.from_installed_pkg_description(ipkg)
    dmeta = to_distutils_meta(meta)

    ret["PKG-INFO"] = StringIO()
    dmeta.write_pkg_file(ret["PKG-INFO"])

    # XXX: bdist_egg includes extra source files here. Should we do the
    # same for compatibility ?
    ret["SOURCES.txt"] = StringIO()
    files = []
    file_sections = ipkg.resolve_paths()
    for name, value in file_sections.items():
        files.extend([f[0] for f in value])
    ret["SOURCES.txt"].writelines("\n".join([os.path.normpath(f) for f in files]))

    if meta.install_requires:
        ret["requires.txt"] = StringIO()
        ret["requires.txt"].write("\n".join(meta.install_requires))

    ret["top_level.txt"] = StringIO()
    ret["top_level.txt"].write("\n".join(meta.top_levels))
    ret["top_level.txt"].write("\n")

    # Write not-zip-safe
    # FIXME: handle this, assume not zip safe for now
    ret["not-zip-safe"] = StringIO()
    ret["not-zip-safe"].write("\n")

    ret["dependency_links.txt"] = StringIO()
    ret["dependency_links.txt"].write("\n")

    ret["entry_points.txt"] = StringIO()
    ret["entry_points.txt"].write("[console_scripts]\n")
    ret["entry_points.txt"].write(
        "\n".join([exe.full_representation() for exe in ipkg.executables.values()]))
    ret["entry_points.txt"].write("\n")

    return ret
