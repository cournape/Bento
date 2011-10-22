import sys
import os
import string
import time

if sys.version_info[0] < 3:
    from StringIO \
        import \
            StringIO
else:
    from io \
        import \
            StringIO

from distutils.util import \
        get_platform
from distutils.sysconfig import \
        get_python_version

from bento._config import \
        WININST_DIR
from bento.core import \
        PackageMetadata
import bento

def wininst_filename(fullname, pyver=None):
    if not pyver:
        pyver = ".".join([str(i) for i in sys.version_info[:2]])
    return "%s-py%s.win32.exe" % (fullname, pyver)

# Stolen from distutils.commands.bdist_wininst
# FIXME: improve this code, in particular integration with
# InstalledPkgDescription

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
    directory = WININST_DIR
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

def create_exe(ipkg, arcname, installer_name, bitmap=None, dist_dir="bento"):
    import struct

    if not os.path.exists(dist_dir):
        os.makedirs(dist_dir)

    cfgdata = get_inidata(ipkg)

    if bitmap:
        bitmapdata = open(bitmap, "rb").read()
        bitmaplen = len(bitmapdata)
    else:
        bitmaplen = 0

    fid = open(installer_name, "wb")
    fid.write(get_exe_bytes())
    if bitmap:
        fid.write(bitmapdata)

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
    fid.write(cfgdata)

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
    fid.write(header)
    fid.write(open(arcname, "rb").read())

def get_inidata(ipkg):
    # Return data describing the installation.
    meta = PackageMetadata.from_ipkg(ipkg)

    # Write the [metadata] section.
    lines = []
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
        if name == "summary":
            name = "description"
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
    # FIXME: handle this correctly
    lines.append("target_compile=1")
    lines.append("target_optimize=1")
    #if self.target_version:
    #    lines.append("target_version=%s" % self.target_version)
    #if self.user_access_control:
    #    lines.append("user_access_control=%s" % self.user_access_control)

    title = meta.fullname
    lines.append("title=%s" % escape(title))
    build_info = "Built %s with bento-%s" % \
                 (time.ctime(time.time()), bento.__version__)
    lines.append("build_info=%s" % build_info)
    return string.join(lines, "\n")
