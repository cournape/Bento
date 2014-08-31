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

    def append(self, var, value, create=False):
        """Append a single item to the variable var."""
        if create:
            cur = self.get(var, [])
            self[var] = cur
        else:
            cur = self[var]
        cur.append(value)

    def append_unique(self, var, value, create=False):
        """Append a single item to the variable var if not already there. Does
        nothing otherwise"""
        if create:
            cur = self.get(var, [])
            self[var] = cur
        else:
            cur = self[var]
        if not value in cur:
            cur.append(value)

    def extend(self, var, values, create=False):
        if create:
            cur = self.get(var, [])
            self[var] = cur
        else:
            cur = self[var]
        cur.extend(values)

    def prepend(self, var, value, create=False):
        """Prepend a single item to the list."""
        if create:
            cur = self.get(var, [])
        else:
            cur = self[var]
        self[var] = [value] + cur

    def prextend(self, var, values, create=False):
        """Prepend a list of values in front of self[var]."""
        if create:
            cur = self.get(var, [])
        else:
            cur = self[var]
        self[var] = values + cur
