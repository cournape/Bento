import os
import re
import subprocess
import _winreg

def open_key(path):
    return _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, path)

def close_key(k):
    return _winreg.CloseKey(k)

def get_output(conf, vcbat, args=None):
    """Parse the output of given bat file, with given args."""
    if args is None:
        args = ""
    cnt = """\
echo @off
set INCLUDE=
set LIB=
call "%(bat)s" %(args)s
echo PATH=%%PATH%%
echo LIB=%%LIB%%
echo INCLUDE=%%INCLUDE%%
""" % {"bat": vcbat, "args": args}
    batnode = conf.bld_root.declare("foo.bat")
    batnode.write(cnt)

    p = subprocess.Popen(["cmd", "/E:one", "/V:on", "/C", batnode.abspath()], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (out, err) = p.communicate()
    for line in out.splitlines():
        if re.match("^Error", line):
            print "Error: %r" % line
            raise RuntimeError("Error while executing bat script: %r" % out)

    res = {"PATH": re.compile("^PATH=(.+)$"),
        "INCLUDE": re.compile("^INCLUDE=(.+)$"),
        "LIB": re.compile("^LIB=(.+)$")}
    ret = {}
    for name, r in res.items():
        for line in out.splitlines():
            m = r.match(line)
            if m:
                v = m.group(1).split(os.pathsep)
                # Is there a better way to avoid spurious empty paths ?
                ret[name] = [x for x in v if x != ""]

    return ret

def read_keys(base, key):
    """Return list of registry keys."""
    try:
        handle = _winreg.OpenKeyEx(base, key)
    except _winreg.error:
        return None
    L = []
    i = 0
    while True:
        try:
            k = _winreg.EnumKey(handle, i)
        except _winreg.error:
            break
        L.append(k)
        i += 1
    return L

def read_values(base, key):
    try:
        handle = _winreg.OpenKeyEx(base, key)
    except _winreg.error:
        return None

    d = {}
    i = 0
    while True:
        try:
            name, value, type = _winreg.EnumValue(handle, i)
        except _winreg.error, e:
            break
        d[convert_mbcs(name)] = convert_mbcs(value)
        i += 1
    return d

def read_value(key, root=_winreg.HKEY_LOCAL_MACHINE):
    base = os.path.dirname(key)
    val = os.path.basename(key)
    try:
        handle = _winreg.OpenKeyEx(root, base)
        try:
            value, type = _winreg.QueryValueEx(handle, val)
            return value
        finally:
            _winreg.CloseKey(handle)
    except _winreg.error:
        return None

def convert_mbcs(s):
    dec = getattr(s, "decode", None)
    if dec is not None:
        try:
            s = dec("mbcs")
        except UnicodeError:
            pass
    return s
