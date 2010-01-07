import os
import sys
import string
import zipfile

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from distutils.util import \
        get_platform
from distutils.sysconfig import \
        get_python_version

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
from toydist.commands.build_egg import \
        write_egg_info, egg_info_dirname

def wininst_filename(fullname, pyver=None):
    if not pyver:
        pyver = ".".join([str(i) for i in sys.version_info[:2]])
    return "%s-py%s.win32.exe" % (fullname, pyver)

class BuildWininstCommand(Command):
    long_descr = """\
Purpose: build wininst
Usage:   toymaker build_wininst [OPTIONS]"""
    short_descr = "build wininst."

    def run(self, opts):
        self.set_option_parser()
        o, a = self.parser.parse_args(opts)
        if o.help:
            self.parser.print_help()
            return

        filename = "installed-pkg-info"
        if not os.path.exists(filename):
            raise UsageException("%s: error: %s subcommand require executed build" \
                    % (SCRIPT_NAME, "build_wininst"))


        ipkg = InstalledPkgDescription.from_file(filename)
        meta = PackageMetadata.from_installed_pkg_description(ipkg)

        # XXX: do this correctly, maybe use same as distutils ?
        arcname = os.path.join("toydist", "yoyo.zip")

        wininst = wininst_filename(os.path.join("toydist", meta.fullname))
        wininst_dir = os.path.dirname(wininst)
        if wininst_dir:
            if not os.path.exists(wininst_dir):
                os.makedirs(wininst_dir)

        egg_info = os.path.join("PURELIB", egg_info_dirname(meta.fullname))

        compression = zipfile.ZIP_DEFLATED
        zid = zipfile.ZipFile(arcname, "w", compression=compression)
        try:
            ret = write_egg_info(ipkg)
            try:
                for k, v in ret.items():
                    v.seek(0)
                    zid.writestr(os.path.join(egg_info, k), v.getvalue())
            finally:
                for v in ret.values():
                    v.close()

            # FIXME: abstract file_sections, it is too low-level ATM, and not
            # very practical to use. In Most installers, what is needed is:
            #  - specify a different install scheme per sectio
            # - ?
            ipkg.path_variables["sitedir"] = "."
            ipkg.path_variables["gendatadir"] = "$sitedir"

            file_sections = ipkg.resolve_paths()
            for type in file_sections:
                if type == "executables":
                    basename = "SCRIPTS"
                    for value in file_sections["executables"].values():
                        for f in value:
                            zid.write(f[0], os.path.join(basename, os.path.basename(f[1])))
                elif type in ["pythonfiles", "datafiles"]:
                    # FIXME: how to deal with data files ? Shall we really
                    # install all of them in sphinx ?
                    basename = "PURELIB"
                    for value in file_sections[type].values():
                        for f in value:
                            zid.write(f[0], os.path.join(basename, f[1]))
                else:
                    for value in file_sections[type].values():
                        for f in value:
                            zid.write(f[0], f[1])
        finally:
            zid.close()

        create_exe(ipkg, arcname, wininst)
        return 

# Stolen from distutils.commands.bdist_wininst

# FIXME: deal with this correctly, in particular MSVC - most likely we will
# need to hardcode things depending on python versions
def get_exe_bytes (target_version=None, plat_name=None):
    if target_version is None:
        target_version = ""
    if plat_name is None:
        plat_name = get_platform()
    from distutils.msvccompiler import get_build_version
    # If a target-version other than the current version has been
    # specified, then using the MSVC version from *this* build is no good.
    # Without actually finding and executing the target version and parsing
    # its sys.version, we just hard-code our knowledge of old versions.
    # NOTE: Possible alternative is to allow "--target-version" to
    # specify a Python executable rather than a simple version string.
    # We can then execute this program to obtain any info we need, such
    # as the real sys.version string for the build.
    cur_version = get_python_version()
    if target_version and target_version != cur_version:
        raise NotImplementedError("target_version handling not implemented yet.")
        # If the target version is *later* than us, then we assume they
        # use what we use
        # string compares seem wrong, but are what sysconfig.py itself uses
        if self.target_version > cur_version:
            bv = get_build_version()
        else:
            if self.target_version < "2.4":
                bv = 6.0
            else:
                bv = 7.1
    else:
        # for current version - use authoritative check.
        bv = get_build_version()

    # wininst-x.y.exe directory
    # XXX: put those somewhere else, and per-python version preferably
    directory = os.path.join(os.path.dirname(__file__), "wininst")
    # we must use a wininst-x.y.exe built with the same C compiler
    # used for python.  XXX What about mingw, borland, and so on?

    # if plat_name starts with "win" but is not "win32"
    # we want to strip "win" and leave the rest (e.g. -amd64)
    # for all other cases, we don't want any suffix
    if plat_name != 'win32' and plat_name[:3] == 'win':
        sfix = plat_name[3:]
    else:
        sfix = ''

    filename = os.path.join(directory, "wininst-%.1f%s.exe" % (bv, sfix))
    return open(filename, "rb").read()

def create_exe(ipkg, arcname, installer_name, bitmap=None, dist_dir="toydist"):
    import struct

    if not os.path.exists(dist_dir):
        os.makedirs(dist_dir)

    cfgdata = get_inidata(ipkg)

    if bitmap:
        bitmapdata = open(bitmap, "rb").read()
        bitmaplen = len(bitmapdata)
    else:
        bitmaplen = 0

    file = open(installer_name, "wb")
    file.write(get_exe_bytes())
    if bitmap:
        file.write(bitmapdata)

    # Convert cfgdata from unicode to ascii, mbcs encoded
    try:
        unicode
    except NameError:
        pass
    else:
        if isinstance(cfgdata, unicode):
            cfgdata = cfgdata.encode("mbcs")

    # Append the pre-install script
    cfgdata = cfgdata + "\0"
    #if self.pre_install_script:
    #    script_data = open(self.pre_install_script, "r").read()
    #    cfgdata = cfgdata + script_data + "\n\0"
    #else:
    #    # empty pre-install script
    #    cfgdata = cfgdata + "\0"
    cfgdata = cfgdata + "\0"
    file.write(cfgdata)

    # The 'magic number' 0x1234567B is used to make sure that the
    # binary layout of 'cfgdata' is what the wininst.exe binary
    # expects.  If the layout changes, increment that number, make
    # the corresponding changes to the wininst.exe sources, and
    # recompile them.
    header = struct.pack("<iii",
                         0x1234567B,       # tag
                         len(cfgdata),     # length
                         bitmaplen,        # number of bytes in bitmap
                         )
    file.write(header)
    file.write(open(arcname, "rb").read())

def get_inidata(ipkg):
    # Return data describing the installation.

    lines = []
    meta = PackageMetadata.from_installed_pkg_description(ipkg)

    # Write the [metadata] section.
    lines.append("[metadata]")

    # 'info' will be displayed in the installer's dialog box,
    # describing the items to be installed.
    info = meta.description + '\n'

    # Escape newline characters
    def escape(s):
        return string.replace(s, "\n", "\\n")

    for name in ["author", "author_email", "summary", "maintainer",
                 "maintainer_email", "name", "url", "version"]:
        data = getattr(meta, name)
        if data:
            info = info + ("\n    %s: %s" % \
                           (string.capitalize(name), escape(data)))
            lines.append("%s=%s" % (name, escape(data)))

    # The [setup] section contains entries controlling
    # the installer runtime.
    lines.append("\n[Setup]")
    # FIXME: handle install scripts
    #if self.install_script:
    #    lines.append("install_script=%s" % self.install_script)
    lines.append("info=%s" % escape(info))
    #lines.append("target_compile=%d" % (not self.no_target_compile))
    #lines.append("target_optimize=%d" % (not self.no_target_optimize))
    #if self.target_version:
    #    lines.append("target_version=%s" % self.target_version)
    #if self.user_access_control:
    #    lines.append("user_access_control=%s" % self.user_access_control)

    title = meta.fullname
    lines.append("title=%s" % escape(title))
    import time
    import toydist
    build_info = "Built %s with distutils-%s" % \
                 (time.ctime(time.time()), toydist.__version__)
    lines.append("build_info=%s" % build_info)
    return string.join(lines, "\n")

