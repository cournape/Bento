import os
import re
import subprocess
import _winreg

import yaku.task
from yaku.tools.mscommon.common \
    import \
        read_values, read_value, get_output

def _exec_command_factory(saved):
    def msvc_exec_command(self, cmd, cwd, env=None):
        new_cmd = []
        carry = ""
        for c in cmd:
            if c in ["/Fo", "/out:", "/OUT:", "/object:"]:
                carry = c
            else:
                c = carry + c
                carry = ""
                new_cmd.append(c)

        env = dict(os.environ)
        env.update(PATH=os.pathsep.join(self.env["PATH"]))
        saved(self, new_cmd, cwd, env=env)
    return msvc_exec_command

# Dict to 'canonalize' the arch
_ARCH_TO_CANONICAL = {
    "amd64"     : "amd64",
    "emt64"     : "amd64",
    "i386"      : "x86",
    "i486"      : "x86",
    "i586"      : "x86",
    "i686"      : "x86",
    "ia64"      : "ia64",
    "itanium"   : "ia64",
    "x86"       : "x86",
    "x86_64"    : "amd64",
}

# Given a (host, target) tuple, return the argument for the bat file. Both host
# and targets should be canonalized.
_HOST_TARGET_ARCH_TO_BAT_ARCH = {
    ("x86", "x86"): "x86",
    ("x86", "amd64"): "x86_amd64",
    ("amd64", "amd64"): "amd64",
    ("amd64", "x86"): "x86",
    ("x86", "ia64"): "x86_ia64"
}

_VCVER = ["10.0", "9.0", "9.0Exp","8.0", "8.0Exp","7.1", "7.0", "6.0"]

_VCVER_TO_PRODUCT_DIR = {
        '10.0': [
            r'Microsoft\VisualStudio\10.0\Setup\VC\ProductDir'],
        '9.0': [
            r'Microsoft\VisualStudio\9.0\Setup\VC\ProductDir'],
        '9.0Exp' : [
            r'Microsoft\VCExpress\9.0\Setup\VC\ProductDir'],
        '8.0': [
            r'Microsoft\VisualStudio\8.0\Setup\VC\ProductDir'],
        '8.0Exp': [
            r'Microsoft\VCExpress\8.0\Setup\VC\ProductDir'],
        '7.1': [
            r'Microsoft\VisualStudio\7.1\Setup\VC\ProductDir'],
        '7.0': [
            r'Microsoft\VisualStudio\7.0\Setup\VC\ProductDir'],
        '6.0': [
            r'Microsoft\VisualStudio\6.0\Setup\Microsoft Visual C++\ProductDir']
}

_is_win64 = None

def is_win64():
    """Return true if running on windows 64 bits.
    
    Works whether python itself runs in 64 bits or 32 bits."""
    # Unfortunately, python does not provide a useful way to determine
    # if the underlying Windows OS is 32-bit or 64-bit.  Worse, whether
    # the Python itself is 32-bit or 64-bit affects what it returns,
    # so nothing in sys.* or os.* help.  

    # Apparently the best solution is to use env vars that Windows
    # sets.  If PROCESSOR_ARCHITECTURE is not x86, then the python
    # process is running in 64 bit mode (on a 64-bit OS, 64-bit
    # hardware, obviously).
    # If this python is 32-bit but the OS is 64, Windows will set
    # ProgramW6432 and PROCESSOR_ARCHITEW6432 to non-null.
    # (Checking for HKLM\Software\Wow6432Node in the registry doesn't
    # work, because some 32-bit installers create it.)
    global _is_win64
    if _is_win64 is None:
        # I structured these tests to make it easy to add new ones or
        # add exceptions in the future, because this is a bit fragile.
        _is_win64 = False
        if os.environ.get('PROCESSOR_ARCHITECTURE','x86') != 'x86':
            _is_win64 = True
        if os.environ.get('PROCESSOR_ARCHITEW6432'):
            _is_win64 = True
        if os.environ.get('ProgramW6432'):
            _is_win64 = True
    return _is_win64


def msvc_version_to_maj_min(msvc_version):
   msvc_version_numeric = ''.join([x for  x in msvc_version if x in string_digits + '.'])

   t = msvc_version_numeric.split(".")
   if not len(t) == 2:
       raise ValueError("Unrecognized version %s (%s)" % (msvc_version,msvc_version_numeric))
   try:
       maj = int(t[0])
       min = int(t[1])
       return maj, min
   except ValueError, e:
       raise ValueError("Unrecognized version %s (%s)" % (msvc_version,msvc_version_numeric))

def is_host_target_supported(host_target, msvc_version):
    """Return True if the given (host, target) tuple is supported given the
    msvc version.

    Parameters
    ----------
    host_target: tuple
        tuple of (canonalized) host-target, e.g. ("x86", "amd64") for cross
        compilation from 32 bits windows to 64 bits.
    msvc_version: str
        msvc version (major.minor, e.g. 10.0)

    Note
    ----
    This only check whether a given version *may* support the given (host,
    target), not that the toolchain is actually present on the machine.
    """
    # We assume that any Visual Studio version supports x86 as a target
    if host_target[1] != "x86":
        maj, min = msvc_version_to_maj_min(msvc_version)
        if maj < 8:
            return False

    return True

def find_vc_pdir(msvc_version):
    """Try to find the product directory for the given
    version.

    Note
    ----
    If for some reason the requested version could not be found, an
    exception which inherits from VisualCException will be raised."""
    base = _winreg.HKEY_LOCAL_MACHINE
    root = 'Software\\'
    if is_win64():
        root = root + 'Wow6432Node\\'
    try:
        hkeys = _VCVER_TO_PRODUCT_DIR[msvc_version]
    except KeyError:
        #debug("Unknown version of MSVC: %s" % msvc_version)
        raise ValueError("Unknown version %s" % msvc_version)

    for key in hkeys:
        key = root + key
        comps = read_value(key)
        if comps is not None:
            if os.path.exists(comps):
                return comps
            else:
                raise ValueError("registry dir %s not found on the filesystem" % comps)
    return None

def find_versions(abi):
    base = _winreg.HKEY_LOCAL_MACHINE
    key = os.path.join(_FC_ROOT[abi], "Fortran")

    availables = {}
    versions = read_keys(base, key)
    if versions is None:
        return availables
    for v in versions:
        verk = os.path.join(key, v)
        key = open_key(verk)
        try:
            maj = _winreg.QueryValueEx(key, "Major Version")[0]
            min = _winreg.QueryValueEx(key, "Minor Version")[0]
            bld = _winreg.QueryValueEx(key, "Revision")[0]
            availables[(maj, min, bld)] = verk
        finally:
            close_key(key)
    return availables

def _detect_msvc(ctx):
    from string import digits as string_digits

    msvc_version_info = (9, 0)
    msvc_version = "9.0"
    pdir = find_vc_pdir(msvc_version)
    if pdir is None:
        raise ValueError("VS 9.0 not found")

    # filter out e.g. "Exp" from the version name
    msvc_ver_numeric = ''.join([x for x in msvc_version if x in string_digits + "."])
    vernum = float(msvc_ver_numeric)
    if 7 <= vernum < 8:
        pdir = os.path.join(pdir, os.pardir, "Common7", "Tools")
        batfilename = os.path.join(pdir, "vsvars32.bat")
    elif vernum < 7:
        pdir = os.path.join(pdir, "Bin")
        batfilename = os.path.join(pdir, "vcvars32.bat")
    else: # >= 8
        batfilename = os.path.join(pdir, "vcvarsall.bat")

    vc_paths = get_output(ctx, batfilename, "x86")
    cc = None
    linker = None
    lib = None
    for p in vc_paths["PATH"]:
        _cc = os.path.join(p, "cl.exe")
        _linker = os.path.join(p, "link.exe")
        _lib = os.path.join(p, "lib.exe")
        if os.path.exists(_cc) and os.path.exists(_linker) and os.path.exists(_lib):
            cc = _cc
            linker = _linker
            lib = _lib
            break
    if cc is None or linker is None:
        raise RuntimeError("Could not find cl.exe/link.exe")

    return cc, linker, lib, vc_paths, msvc_version_info

def setup(ctx):
    env = ctx.env

    cc, linker, lib, vc_paths, msvc_version_info = _detect_msvc(ctx)
    ctx.env["PATH"] = vc_paths["PATH"][:]
    ctx.env.prextend("CPPPATH", vc_paths["INCLUDE"], create=True)
    ctx.env.prextend("LIBDIR", vc_paths["LIB"], create=True)

    ctx.env["CC"] = [cc]
    ctx.env["CC_TGT_F"] = ["/c", "/Fo"]
    ctx.env["CC_SRC_F"] = []
    ctx.env["CFLAGS"] = ["/nologo"]
    ctx.env["CPPPATH_FMT"] = "/I%s"
    ctx.env["DEFINES"] = []
    ctx.env["DEFINES_FMT"] = "/D%s"
    ctx.env["LINK"] = [linker]
    ctx.env["LINK_TGT_F"] = ["/out:"]
    ctx.env["LINK_SRC_F"] = []
    ctx.env["LINKFLAGS"] = ["/nologo"]
    ctx.env["SHLINK"] = [linker, "/DLL"]
    ctx.env["SHLINK_TGT_F"] = ["/out:"]
    ctx.env["SHLINK_SRC_F"] = []
    ctx.env["SHLINKFLAGS"] = []
    ctx.env["MODLINK"] = [linker, "/DLL"]
    ctx.env["MODLINK_TGT_F"] = ["/out:"]
    ctx.env["MODLINK_SRC_F"] = []
    ctx.env["MODLINKFLAGS"] = ["/nologo"]
    ctx.env["LIBS"] = []
    ctx.env["LIB_FMT"] = "%s.lib"
    ctx.env["LIBDIR"] = []
    ctx.env["LIBDIR_FMT"] = "/LIBPATH:%s"

    ctx.env["STLINK"] = [lib]
    ctx.env["STLINK_TGT_F"] = ["/OUT:"]
    ctx.env["STLINK_SRC_F"] = []
    ctx.env["STLINKFLAGS"] = ["/nologo"]
    ctx.env["STATICLIB_FMT"] = "%s.lib"

    ctx.env["CXX"] = [cc]
    ctx.env["CXX_TGT_F"] = ["/c", "/Fo"]
    ctx.env["CXX_SRC_F"] = []
    ctx.env["CXXFLAGS"] = ["/nologo"]
    if msvc_version_info >= (9, 0):
        ctx.env.append("CXXFLAGS", "/EHsc")
    ctx.env["CXXLINK"] = [linker]
    ctx.env["CXXLINKFLAGS"] = ["/nologo"]
    ctx.env["CXXLINK_TGT_F"] = ["/out:"]
    ctx.env["CXXLINK_SRC_F"] = []
    ctx.env["CXXSHLINK"] = [linker]
    ctx.env["CXXSHLINKFLAGS"] = []
    ctx.env["CXXSHLINK_TGT_F"] = ["/out:"]
    ctx.env["CXXSHLINK_SRC_F"] = []

    ctx.env["CC_OBJECT_FMT"] = "%s.obj"
    ctx.env["CXX_OBJECT_FMT"] = "%s.obj"
    ctx.env["SHAREDLIB_FMT"] = "%s.dll"
    ctx.env["PROGRAM_FMT"] = "%s.exe"

    for k, v in vc_paths.items():
        k = k.encode("ascii")
        if k in ["LIB"]:
            env.extend("LIBDIR", v, create=True)
        elif k in ["CPPPATH"]:
            env.extend(k, v, create=True)

for task_class in ["cc", "shcc", "cc_shlink", "cc_stlink", "cc_program", "cxx", "cxxprogram", "pycc", "pycxx", "pylink"]:
    klass = yaku.task.task_factory(task_class)
    saved = klass.exec_command
    klass.exec_command = _exec_command_factory(saved)

def detect(ctx):
    _detect_msvc(ctx)
    return True
