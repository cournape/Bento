import sys
import os
import _winreg

import yaku.utils
import yaku.task

from yaku.tools.mscommon.common \
    import \
        read_keys, open_key, close_key, get_output, parse_output
from yaku.tools.msvc \
    import \
        _exec_command_factory

_ROOT = {"amd64": r"Software\Wow6432Node\Intel\Suites",
         "ia32": r"Software\Intel\Compilers"}

_FC_ROOT = {"amd64": r"Software\Wow6432Node\Intel\Compilers",
         "ia32": r"Software\Intel\Compilers"}

_ABI2BATABI = {"amd64": "intel64", "ia32": "ia32"}

def find_versions_fc(abi):
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

def product_dir_fc(root):
    k = open_key(root)
    try:
        return _winreg.QueryValueEx(k, "ProductDir")[0]
    finally:
        close_key(k)

def setup(ctx):
    env = ctx.env

    env.update(
       {"F77": ["ifort"],
        "F77_LINK": ["ifort"],
        "F77_LINKFLAGS": [],
        "F77FLAGS": [],
        "F77_TGT_F": ["-o"],
        "F77_SRC_F": ["-c"],
        "F77_LINK_TGT_F": ["-o"],
        "F77_LINK_SRC_F": [],
        "F77_OBJECT_FMT": "%s.o",
        "F77_PROGRAM_FMT": "%s"})
    if sys.platform == "win32":
        env.update(
           {"F77FLAGS": ["/nologo"],
            "F77_TGT_F": ["/object:"],
            "F77_SRC_F": ["/c"],
            "F77_LINKFLAGS": ["/nologo"],
            "F77_LINK_TGT_F": ["/link", "/out:"],
            "F77_OBJECT_FMT": "%s.obj",
            "F77_PROGRAM_FMT": "%s.exe"})

        abi = "amd64"

        availables = find_versions_fc(abi)
        if len(availables) < 1:
            raise ValueError("No ifort version found for abi %s" % abi)

        versions = sorted(availables.keys())[::-1]
        pdir = product_dir_fc(availables[versions[0]])
        batfile = os.path.join(pdir, "bin", "ifortvars.bat")

        out = get_output(batfile, _ABI2BATABI[abi])
        d = parse_output(out)
        intel_env = {}
        for k, v in d.items():
            #old = os.environ.get(k, None)
            #if old is None:
            #    old = []
            #else:
            #    old = old.split(os.pathsep)
            #intel_env[k] = os.pathsep.join(list(set(v).difference(old))).encode("mbcs")
            intel_env[k] = os.pathsep.join(v).encode("mbcs")
        env["ENV"] = intel_env

    init()

def init():
    if sys.platform == "win32":
        for task_class in ["f77", "fprogram"]:
           klass = yaku.task.task_factory(task_class)
           saved = klass.exec_command
           klass.exec_command = _exec_command_factory(saved)

def detect(ctx):
    if yaku.utils.find_program("ifort") is None:
        return False
    else:
        return True
