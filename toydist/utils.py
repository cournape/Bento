import os
import sys
import re
import glob
import marshal

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from os.path import \
    join, split, splitext, dirname, relpath
# XXX: implementation details from py_compile
from py_compile import \
    wr_long, MAGIC
import __builtin__

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
        raise ValueError("no files following pattern %s found" % pattern)

    if ref_dir:
        return [relpath(i, ref_dir) for i in matched]
    else:
        return matched

def subst_vars (s, local_vars):
    """Perform shell/Perl-style variable substitution.

    Every occurrence of '$' followed by a name is considered a variable, and
    variable is substituted by the value found in the `local_vars' dictionary.
    Raise ValueError for any variables not found in `local_vars'.

    Parameters
    ----------
    s: str
        variable to substitute
    local_vars: dict
        dict of variables
    """
    def _subst (match, local_vars=local_vars):
        var_name = match.group(1)
        if var_name in local_vars:
            return str(local_vars[var_name])
        else:
            raise ValueError("Invalid variable '$%s'" % var_name)

    def _do_subst(v):
        return re.sub(r'\$([a-zA-Z_][a-zA-Z_0-9]*)', _subst, v)

    try:
        ret = _do_subst(s)
        # Brute force: we keep interpolating until the returned string is the
        # same as the input to handle recursion
        while not ret == s:
            s = ret
            ret = _do_subst(s)
        return ret
    except KeyError, var:
        raise ValueError("invalid variable '$%s'" % var)


if __name__ == "__main__":
    print expand_glob("*.py", dirname(__file__))

def find_package(pkg_name, basedir=''):
    """Given a python package name, find all its modules relatively to basedir.

    If basedir is not given, look relatively to the current directory."""
    # XXX: this function is wrong - use the code from setuptools
    pkg_dir = pkg_name.replace(".", os.path.sep)
    basedir = os.path.join(basedir, pkg_dir)
    init = os.path.join(basedir, '__init__.py')
    if not os.path.exists(init):
        raise ValueError(
                "Missing __init__.py in package %s (in directory %s)"
                % (pkg_name, basedir))
    return [os.path.join(basedir, f)
                for f in
                    os.listdir(os.path.dirname(init)) if f.endswith('.py')]

def prune_file_list(files, redundant):
    """Prune a list of files relatively to a second list.

    Return a subsequence of `files' which contains only files not in
    `redundant'

    Parameters
    ----------
    files: seq
        list of files to prune.
    redundant: seq
        list of candidate files to prune.
    """
    files_set = set([os.path.normpath(f) for f in files])
    redundant_set = set([os.path.normpath(f) for f in redundant])

    return list(files_set.difference(redundant_set))

# Utils to compile .py to .pyc inside zip file
# XXX: this is implementation detail of .pyc, copied from py_compile.py.
# Unfortunately, there is no way that I know of to write the bytecode into a
# string to be used by ZipFile (using compiler is way too slow). Also, the
# py_compile code has not changed much for 10 years.
def compile(source):
    """Return the compiled bytecode from the given filename as a string ."""
    f = open(source, 'U')
    try:
        try:
            timestamp = long(os.fstat(f.fileno()).st_mtime)
        except AttributeError:
            timestamp = long(os.stat(file).st_mtime)
        codestring = f.read()
        f.close()
        if codestring and codestring[-1] != '\n':
            codestring = codestring + '\n'
        try:
            codeobject = __builtin__.compile(codestring, source, 'exec')
        except Exception,err:
            py_exc = PyCompileError(err.__class__, err.args, source)
            if doraise:
                raise py_exc
            else:
                sys.stderr.write(py_exc.msg + '\n')
                return
        fc = StringIO()
        try:
            fc.write('\0\0\0\0')
            wr_long(fc, timestamp)
            fc.write(marshal.dumps(codeobject))
            fc.flush()
            fc.seek(0, 0)
            fc.write(MAGIC)
            return fc.getvalue()
        finally:
            fc.close()
    finally:
        f.close()
