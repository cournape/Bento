import os
import sys
import distutils.unixccompiler
import distutils.ccompiler
import distutils.sysconfig

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
}

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
    env = {
            "LIBS": [],
            "INCPATH_FMT": "-I%s",
            "LIBPATH_FMT": "-L%s",
            "LIBS_FMT": "-l%s",
            "CPPDEF_FMT": "-D%s",
            }
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
        # XXX: not tested
        compiler = distutils.ccompiler.new_compiler(
                compiler=compiler_type)
        compiler.initialize()
        for k, v in MSVC_ENV_ATTR.items():
            env[k] = getattr(compiler, v)
        env.update({"LIBS": [],
                "INCPATH_FMT": "/I%s",
                "LIBPATH_FMT": "/L%s",
                "LIBS_FMT": "%s.lib",
                "CPPDEF_FMT": "/D%s"})
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
