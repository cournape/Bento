import os
import re
import subprocess
import _winreg

def open_key(path):
    return _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, path)

def close_key(k):
    return _winreg.CloseKey(k)

def get_output(vcbat, args=None, env=None):
    """Parse the output of given bat file, with given args."""
    if args is not None:
        #debug("Calling '%s %s'" % (vcbat, args))
        popen = subprocess.Popen('"%s" %s & set' % (vcbat, args),
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 env=env)
    else:
        #debug("Calling '%s'" % vcbat)
        popen = subprocess.Popen('"%s" & set' % vcbat,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 env=env)

    # Use the .stdout and .stderr attributes directly because the
    # .communicate() method uses the threading module on Windows
    # and won't work under Pythons not built with threading.
    stdout = popen.stdout.read()
    if popen.wait() != 0:
        raise IOError(popen.stderr.read().decode("mbcs"))

    output = stdout.decode("mbcs")
    return output

def parse_output(output, keep=("INCLUDE", "LIB", "LIBPATH", "PATH")):
    # dkeep is a dict associating key: path_list, where key is one item from
    # keep, and pat_list the associated list of paths

    dkeep = dict([(k, []) for k in keep])

    # rdk will  keep the regex to match the .bat file output line starts
    rdk = {}
    for k in keep:
        rdk[k] = re.compile('%s=(.*)' % k, re.I)

    def add_env(rmatch, key, dkeep=dkeep):
        plist = rmatch.group(1).split(os.pathsep)
        for p in plist:
            # Do not add empty paths (when a var ends with ;)
            if p:
                p = p.encode('mbcs')
                # XXX: For some reason, VC98 .bat file adds "" around the PATH
                # values, and it screws up the environment later, so we strip
                # it. 
                p = p.strip('"')
                dkeep[key].append(p)

    for line in output.splitlines():
        for k,v in rdk.items():
            m = v.match(line)
            if m:
                add_env(m, k)

    return dkeep

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
