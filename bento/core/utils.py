import os
import sys
import re
import glob
import shutil
import errno

from itertools import izip, imap
from copy import deepcopy

from os.path import \
    join, split, splitext, dirname

from bento.compat.api \
    import \
        relpath, rename as _rename
from bento.core.errors \
    import \
        InvalidPackage

# Color handling for terminals (taken from waf)
COLORS_LST = {
        'USE' : True,
        'BOLD'  :'\x1b[01;1m',
        'RED'   :'\x1b[01;31m',
        'GREEN' :'\x1b[32m',
        'YELLOW':'\x1b[33m',
        'PINK'  :'\x1b[35m',
        'BLUE'  :'\x1b[01;34m',
        'CYAN'  :'\x1b[36m',
        'NORMAL':'\x1b[0m',
        'cursor_on'  :'\x1b[?25h',
        'cursor_off' :'\x1b[?25l',
}

GOT_TTY = not os.environ.get('TERM', 'dumb') in ['dumb', 'emacs']
if GOT_TTY:
    try:
        GOT_TTY = sys.stderr.isatty()
    except AttributeError:
        GOT_TTY = False
if not GOT_TTY or 'NOCOLOR' in os.environ:
    COLORS_LST['USE'] = False

def get_color(cl):
    if not COLORS_LST['USE']:
        return ''
    return COLORS_LST.get(cl, '')

class foo(object):
    def __getattr__(self, a):
        return get_color(a)
    def __call__(self, a):
        return get_color(a)
COLORS = foo()

def pprint(color, str):
    sys.stderr.write('%s%s%s\n' % (COLORS(color), str, COLORS('NORMAL')))

HAS_WILDCARD = re.compile("\*")

def validate_glob_pattern(pattern):
    head, tail = split(pattern) 
    m = HAS_WILDCARD.search(head)
    if m:
        raise ValueError("Wildcard detected in directory for pattern %s" % pattern)
    ext = splitext(tail)[1]
    m = HAS_WILDCARD.search(ext)
    if m:
        raise ValueError("Wildcard detected in extension for pattern %s" % pattern)

def expand_glob(pattern, ref_dir=None):
    """Expand list of files matching the given pattern, relatively to ref_dir.

    If no file is matched, a ValueError is raised.
    """
    validate_glob_pattern(pattern)
    if ref_dir:
        glob_pattern = join(ref_dir, pattern)
    else:
        glob_pattern = pattern
    matched = glob.glob(glob_pattern)
    if len(matched) < 1:
        raise IOError("no files following pattern %s found" % pattern)

    if ref_dir:
        return [relpath(i, ref_dir) for i in matched]
    else:
        return matched

_IDPATTERN = "[a-zA-Z_][a-zA-Z_0-9]*"
_DELIM = "$"

def _simple_subst_vars(s, local_vars):
    """Like subst_vars, but does not handle escaping."""
    def _subst(m):
        var_name = m.group(1)
        if var_name in local_vars:
            return local_vars[var_name]
        else:
            raise ValueError("%s not defined" % var_name)
        
    def _resolve(d):
        ret = {}
        for k, v in d.items():
            ret[k] = re.sub("\%s(%s)" % (_DELIM, _IDPATTERN), _subst, v)
        return ret

    ret = _resolve(s)
    while not ret == s:
        s = ret
        ret = _resolve(s)
    return ret

def subst_vars (s, local_vars):
    """Perform shell/Perl-style variable substitution.

    Every occurrence of '$' followed by a name is considered a variable, and
    variable is substituted by the value found in the `local_vars' dictionary.
    Raise ValueError for any variables not found in `local_vars'.

    '$' may be escaped by using '$$'

    Parameters
    ----------
    s: str
        variable to substitute
    local_vars: dict
        dict of variables
    """
    # Resolve variable substitution within the local_vars dict
    local_vars = _simple_subst_vars(local_vars, local_vars)

    def _subst (match):
        named = match.group("named")
        if named is not None:
            if named in local_vars:
                return str(local_vars[named])
            else:
                raise ValueError("Invalid variable '%s'" % named)
        if match.group("escaped") is not None:
            return _DELIM
        raise ValueError("This should not happen")

    def _do_subst(v):
        pattern_s = r"""
        %(delim)s(?:
            (?P<escaped>%(delim)s) |
            (?P<named>%(id)s)
        )""" % {"delim": r"\%s" % _DELIM, "id": _IDPATTERN}
        pattern = re.compile(pattern_s, re.VERBOSE)
        return pattern.sub(_subst, v)

    try:
        return _do_subst(s)
    except KeyError, var:
        raise ValueError("invalid variable '$%s'" % var)

# Taken from multiprocessing code
def cpu_count():
    '''
    Returns the number of CPUs in the system
    '''
    if sys.platform == 'win32':
        try:
            num = int(os.environ['NUMBER_OF_PROCESSORS'])
        except (ValueError, KeyError):
            num = 0
    elif 'bsd' in sys.platform or sys.platform == 'darwin':
        try:
            num = int(os.popen('sysctl -n hw.ncpu').read())
        except ValueError:
            num = 0
    else:
        try:
            num = os.sysconf('SC_NPROCESSORS_ONLN')
        except (ValueError, OSError, AttributeError):
            num = 0

    if num >= 1:
        return num
    else:
        return 1
        #raise NotImplementedError('cannot determine number of cpus')

if __name__ == "__main__":
    print expand_glob("*.py", dirname(__file__))

def validate_package(pkg_name, basedir):
    """Given a python package name, check whether it is indeed an existing
    package.

    Package is looked relatively to the current directory."""
    # XXX: this function is wrong - use the code from setuptools
    pkg_dir = pkg_name.replace(".", os.path.sep)
    basedir = os.path.join(basedir, pkg_dir)
    init = os.path.join(basedir, '__init__.py')
    if not os.path.exists(init):
        raise InvalidPackage(
                "Missing __init__.py in package %s (in directory %s)"
                % (pkg_name, basedir))
    return basedir

def find_package(pkg_name, basedir=''):
    """Given a python package name, find all its modules relatively to basedir.

    If basedir is not given, look relatively to the current directory."""
    basedir = validate_package(pkg_name, basedir)
    return [os.path.join(basedir, f)
                for f in
                    os.listdir(basedir) if f.endswith('.py')]

def ensure_dir(path):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d)

def normalize_path(path):
    return path.replace("\\", "/")

def unnormalize_path(path):
    return path.replace("/", "\\")

def resolve_glob(files, reference_path=None):
    """Resolve all glob patterns in the given list

    Parameters
    ----------
    files: seq
    """
    ret = []
    for f in files:
        ret.extend(expand_glob(f, reference_path))
    return ret

# Code by Armin Ronacher
missing = object()
class OrderedDict(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self)
        self._keys = []
        self.update(*args, **kwargs)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self._keys.remove(key)

    def __setitem__(self, key, item):
        if key not in self:
            self._keys.append(key)
        dict.__setitem__(self, key, item)

    def __deepcopy__(self, memo=None):
        if memo is None:
            memo = {}
        d = memo.get(id(self), missing)
        if d is not missing:
            return d
        memo[id(self)] = d = self.__class__()
        dict.__init__(d, deepcopy(self.items(), memo))
        d._keys = self._keys[:]
        return d

    def __getstate__(self):
        return {'items': dict(self), 'keys': self._keys}

    def __setstate__(self, d):
        self._keys = d['keys']
        dict.update(d['items'])

    def __reversed__(self):
        return reversed(self._keys)

    def __eq__(self, other):
        if isinstance(other, odict):
            if not dict.__eq__(self, other):
                return False
            return self.items() == other.items()
        return dict.__eq__(self, other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __cmp__(self, other):
        if isinstance(other, odict):
            return cmp(self.items(), other.items())
        elif isinstance(other, dict):
            return dict.__cmp__(self, other)
        return NotImplemented

    @classmethod
    def fromkeys(cls, iterable, default=None):
        return cls((key, default) for key in iterable)

    def clear(self):
        del self._keys[:]
        dict.clear(self)

    def copy(self):
        return self.__class__(self)

    def items(self):
        return zip(self._keys, self.values())

    def iteritems(self):
        return izip(self._keys, self.itervalues())

    def keys(self):
        return self._keys[:]

    def iterkeys(self):
        return iter(self._keys)

    def pop(self, key, default=missing):
        if default is missing:
            return dict.pop(self, key)
        elif key not in self:
            return default
        self._keys.remove(key)
        return dict.pop(self, key, default)

    def popitem(self, key):
        self._keys.remove(key)
        return dict.popitem(key)

    def setdefault(self, key, default=None):
        if key not in self:
            self._keys.append(key)
        dict.setdefault(self, key, default)

    def update(self, *args, **kwargs):
        sources = []
        if len(args) == 1:
            if hasattr(args[0], 'iteritems'):
                sources.append(args[0].iteritems())
            else:
                sources.append(iter(args[0]))
        elif args:
            raise TypeError('expected at most one positional argument')
        if kwargs:
            sources.append(kwargs.iteritems())
        for iterable in sources:
            for key, val in iterable:
                self[key] = val

    def values(self):
        return map(self.get, self._keys)

    def itervalues(self):
        return imap(self.get, self._keys)

    def index(self, item):
        return self._keys.index(item)

    def byindex(self, item):
        key = self._keys[item]
        return (key, dict.__getitem__(self, key))

    def reverse(self):
        self._keys.reverse()

    def sort(self, *args, **kwargs):
        self._keys.sort(*args, **kwargs)

def rename(source, target):
    try:
        _rename(source, target)
    except OSError, e:
        if e.errno == errno.EXDEV:
            shutil.move(source, target)
        else:
            raise
