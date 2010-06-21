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

UNIX_ENV_ATTR = {
        "CC": "compiler",
        "CXX": "compiler_cxx",
        "CCSHARED": "compiler_so",
        "LDSHARED": "linker_so",
        "LINKCC": "linker_exe",
}

MSVC_ENV_ATTR = {
        "CC": "cc",
        "CXX": "cc",
        "CFLAGS": "compile_options",
        "LDSHARED": "linker",
        "LINKCC": "linker",
}

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

    # Unix-like default (basically works everwhere but windows)
    env = {"PYCC_NAME": compiler_type}
    if compiler_type == "unix":
        for k in ["CC", "CXX", "OPT", "CFLAGS", "CCSHARED",
                  "LDSHARED", "SO", "LINKCC"]:
            var = distutils.sysconfig.get_config_var(k)
            # FIXME: Splitting most likely needs to be smarter to take
            # quote into account - OTOH, many compilers don't handle
            # quote in directories/CPP variables (Does C89 say
            # something about it ?)
            env[k] = var.split(" ")
    elif compiler_type == "msvc":
        env["SO"] = ".pyd"
        try:
            setup_msvc(env)
        except errors.DistutilsPlatformError, e:
            setup_mingw(env)
    else:
        compiler = distutils.ccompiler.new_compiler(
                compiler=compiler_type)
        # If not a UnixCCompiler instance, we have no clue how to deal
        # with it
        if not isinstance(compiler,
                distutils.unixccompiler.UnixCCompiler):
            raise ValueError("We don't know how to deal with %s instances" % compiler.__class__)
        # XXX: in this case, CC and co contains both the compiler and
        # the options. Distutils is so fucked up...
        for k, v in UNIX_ENV_ATTR.items():
            env[k] = getattr(compiler, v)
        env["CFLAGS"] = []
        env["CXXFLAGS"] = []

        if compiler_type == "mingw32":
            env["LIBS"] = compiler.dll_libraries or []

    return env

def _get_ext_library_dirs():
    binst = build_ext.build_ext(dist.Distribution())
    binst.initialize_options()
    binst.finalize_options()
    return binst.library_dirs

def setup_msvc(env):
    compiler = distutils.ccompiler.new_compiler(
            compiler="msvc")
    compiler.initialize()

    for k, v in MSVC_ENV_ATTR.items():
        env[k] = getattr(compiler, v)
    env["LDSHARED"] = [env["LDSHARED"]] + compiler.ldflags_shared
    env["CCSHARED"] = []
    env["OPT"] = compiler.compile_options
    env["LIBDIR"] = _get_ext_library_dirs()
