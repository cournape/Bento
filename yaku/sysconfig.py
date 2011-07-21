import os
import sys
import distutils.unixccompiler
import distutils.ccompiler
import distutils.sysconfig
import distutils.command.build_ext as build_ext
import distutils.dist as dist

from distutils \
    import \
        errors
from distutils \
    import \
        sysconfig

DEFAULT_COMPILERS = {
        "win32": [None, "mingw32"],
        "default": [None]
}

def _mingw32_cc():
    compiler_type = "mingw32"
    compiler = distutils.ccompiler.new_compiler(compiler=compiler_type)
    return compiler.compiler_so

def detect_distutils_cc(ctx):
    if not sys.platform in DEFAULT_COMPILERS:
        plat = "default"
    else:
        plat = sys.platform

    sys.stderr.write("Detecting distutils C compiler... ")
    compiler_type = \
            distutils.ccompiler.get_default_compiler()
    if sys.platform == "win32":
        if compiler_type == "msvc":
            try:
                compiler = distutils.ccompiler.new_compiler(
                        compiler="msvc")
                compiler.initialize()
                cc = [compiler.cc]
            except errors.DistutilsPlatformError:
                cc = _mingw32_cc()
        else:
            cc = _mingw32_cc()
    else:
        cc = distutils.sysconfig.get_config_var("CC")
        # FIXME: use shlex for proper escaping handling
        cc = cc.split()
    sys.stderr.write("%s\n" % compiler_type)
    return cc

# XXX: unixccompiler instances are the only classes where we can hope
# to get semi-sensical data. Reusing them also makes transition easier
# for packagers, as their compilation options will be reused.
# OTOH, having a sane tooling system will make customization much
# easier.
def get_configuration(compiler_type=None):
    plat = os.name
    if compiler_type is None:
        compiler_type = distutils.ccompiler.get_default_compiler(plat)

    if not compiler_type in distutils.ccompiler.compiler_class:
        raise ValueError("compiler type %s is not recognized" %
                         compiler_type)

    env = {"CC": [],
        "CPPPATH": [],
        "BASE_CFLAGS": [],
        "OPT": [],
        "SHARED": [],
        "CFLAGS": [],
        "SHLINK": [],
        "LDFLAGS": [],
        "LIBDIR": [],
        "LIBS": [],
        "SO": ""}

    env["CPPPATH"].append(sysconfig.get_python_inc())
    if compiler_type == "unix":
        env["CC"].extend(sysconfig.get_config_var("CC").split(" "))
        env["BASE_CFLAGS"].extend(sysconfig.get_config_var("BASECFLAGS").split(" "))
        env["OPT"].extend(sysconfig.get_config_var("OPT").split(" "))
        env["SHARED"].extend(sysconfig.get_config_var("CCSHARED").split(" "))

        env["SHLINK"] = sysconfig.get_config_var("LDSHARED").split(" ")
        env["SO"] = sysconfig.get_config_var("SO")
        env["LDFLAGS"] = sysconfig.get_config_var("LDFLAGS").split()
        if "-pthread" in sysconfig.get_config_var("LDFLAGS"):
            env["LDFLAGS"].insert(0, "-pthread")
        env["CFLAGS"].extend(sysconfig.get_config_var("CFLAGS").split(" "))
        env["FRAMEWORKS"] = []
        setup_unix(env)
    elif compiler_type == "msvc":
        setup_msvc(env)
    elif compiler_type == "mingw32":
        setup_mingw32(env)
    else:
        raise ValueError("Gne ?")

    return env

def _get_ext_library_dirs():
    binst = build_ext.build_ext(dist.Distribution())
    binst.initialize_options()
    binst.finalize_options()
    return binst.library_dirs

def _get_ext_libraries(compiler):
    binst = build_ext.build_ext(dist.Distribution())
    binst.compiler = compiler
    binst.initialize_options()
    binst.finalize_options()
    class _FakeExt(object):
        def __init__(self):
            self.libraries = []
    return binst.get_libraries(_FakeExt())

def setup_unix(env):
    if sys.platform == "darwin":
        env["LDFLAGS"].extend(["-bundle", "-undefined", "dynamic_lookup"])

        def _strip_arch(flag):
            value = env[flag]
            while "-arch" in value:
                id = value.index("-arch")
                value.pop(id)
                value.pop(id)
            return value
        for flag in ["BASE_CFLAGS", "LDFLAGS"]:
            env[flag] = _strip_arch(flag)

def setup_msvc(env):
    compiler = distutils.ccompiler.new_compiler(
            compiler="msvc")
    compiler.initialize()

    env["CC"] = compiler.cc
    env["BASE_CFLAGS"].extend(compiler.compile_options)

    env["SHLINK"] = compiler.linker
    env["SO"] = ".pyd"
    env["LDFLAGS"] = compiler.ldflags_shared
    env["LIBDIR"].extend( _get_ext_library_dirs())

def setup_mingw32(env):
    compiler = distutils.ccompiler.new_compiler(
            compiler="mingw32")

    env["CC"] = ["gcc"]
    env["BASE_CFLAGS"].extend(["-mno-cygwin"])

    env["SHLINK"] = ["gcc", "-mno-cygwin", "-shared"]
    env["SO"] = ".pyd"
    #env["LDFLAGS"] = compiler.ldflags_shared
    env["LIBDIR"].extend( _get_ext_library_dirs())

    libs = _get_ext_libraries(compiler)
    libs += compiler.dll_libraries 
    env["LIBS"].extend(libs)
