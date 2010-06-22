import re
import os

from yaku.utils \
    import \
    ensure_dir, rename

re_imp = re.compile('^(#)*?([^#=]*?)\ =\ (.*?)$', re.M)

class Environment(dict):
    def get_flat(self, k):
        s = self[k]
        if isinstance(s, str):
            return s
        else:
            return " ".join(s)

    def store(self, filename):
        tmp = filename + ".tmp"
        ensure_dir(tmp)
        fid = open(tmp, "w")
        try:
            for k in sorted(self.keys()):
                fid.write("%s = %r\n" % (k, self[k]))
        finally:
            fid.close()
        rename(tmp, filename)

    def load(self, filename):
        f = open(filename)
        for m in re_imp.finditer(f.read()):
            self[m.group(2)] = eval(m.group(3))
