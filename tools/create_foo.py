import os
import re
import sys
import StringIO
from hashlib import md5

VERSION = "1"

def sfilter(path):
    f = open(path, "r")
    cnt = f.read()
    f.close()

    #cnt = process_decorators(cnt)
    #cnt = process_imports(cnt)
    #if path.endswith('Options.py') or path.endswith('Scripting.py'):
    #   cnt = cnt.replace('Utils.python_24_guard()', '')

    return (StringIO.StringIO(cnt), len(cnt), cnt)

def translate_entry_point(s):
    module, func = s.split(":", 1)
    return "import %s\n%s.%s()" % (module, module, func)

def read_config():
    import ConfigParser
    s = ConfigParser.ConfigParser()
    s.read("config.ini")

    ret = {}
    if not len(s.sections()) == 1:
        raise ValueError("Only one section supported for now")
    section = s.sections()[0]
    ret["script_template"] = s.get(section, "template")
    ret["script_name"] = s.get(section, "script_name")
    ret["script_pkg_root"] = s.get(section, "package_root")
    ret["script_version"] = s.get(section, "version")
    ret["script_entry_point"] = translate_entry_point(s.get(section, "entry_point"))
    ret["packages"] = [i.strip() for i in s.get(section, "packages").split(",")]
    ret["include_exe"] = s.getboolean(section, "include_exe")
    return ret

def create_script_light(tpl, variables):
    f = open(tpl, "r")
    try:
        cnt = f.read()
        r = {}
        for k, v in variables.items():
            r[k] = re.compile("@%s@" % k)
        for k, v in variables.items():
            cnt = r[k].sub(v, cnt)
        return cnt
    finally:
        f.close()

def create_script():
    import tarfile, re

    config = read_config()
    script_name = config["script_name"]
    include_exe = config["include_exe"]

    print "-> Creating script"
    mw = "tmp-foo-" + VERSION

    zip_type = "bz2"

    tar = tarfile.open('%s.tar.%s' % (mw, zip_type), "w:%s" % zip_type)
    tar_files = []

    dirs = [s.replace(".", os.sep) for s in config["packages"]]
    files = []
    for d in dirs:
        for k in os.listdir(d):
            if k.endswith('.py'):
                files.append(os.path.join(d, k))
            if include_exe:
                if k.endswith('.exe'):
                    files.append(os.path.join(d, k))

    for x in files:
        tarinfo = tar.gettarinfo(x, x)
        tarinfo.uid = tarinfo.gid = 1000
        tarinfo.uname = tarinfo.gname = "baka"
        (code, size, cnt) = sfilter(x)
        tarinfo.size = size
        tar.addfile(tarinfo, code)
    tar.close()

    variables = {}
    for k in ["script_name", "script_pkg_root", "script_version", "script_entry_point"]:
        variables[k] = config[k]
    variables["script_name"] = "'%s'" % variables["script_name"]
    variables["script_pkg_root"] = "'%s'" % variables["script_pkg_root"]

    code1 = create_script_light(config["script_template"], variables)

    f = open("%s.tar.%s" % (mw, zip_type), 'rb')
    cnt = f.read()
    f.close()

    def find_unused(kd, ch):
        for i in xrange(35, 125):
            for j in xrange(35, 125):
                if i==j: continue
                if i == 39 or j == 39: continue
                if i == 92 or j == 92: continue
                s = chr(i) + chr(j)
                if -1 == kd.find(s):
                    return (kd.replace(ch, s), s)
        raise

    m = md5()
    m.update(cnt)
    REVISION = m.hexdigest()
    reg = re.compile('^REVISION=(.*)', re.M)
    code1 = reg.sub(r'REVISION="%s"' % REVISION, code1)

    # The reverse order prevent collisions
    (cnt, C2) = find_unused(cnt, '\r')
    (cnt, C1) = find_unused(cnt, '\n')
    f = open(script_name, 'wb')
    f.write(code1.replace("C1='x'", "C1='%s'" % C1).replace("C2='x'", "C2='%s'" % C2))
    f.write('#==>\n')
    f.write('#')
    f.write(cnt)
    f.write('\n')
    f.write('#<==\n')
    f.close()

    if sys.platform != 'win32':
        os.chmod(script_name, 0755)
    os.unlink('%s.tar.%s' % (mw, zip_type))

create_script()
#s = create_script_light("foo-light.in")
#print open(s).read()
