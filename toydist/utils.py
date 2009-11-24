import os
import sys
import re
import glob

from os.path import \
    join, split, splitext, dirname, relpath

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
    sys.stderr.write('%s%s%s' % (COLORS(color), str, COLORS('NORMAL')))

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
