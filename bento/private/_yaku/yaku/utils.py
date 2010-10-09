import sys
import re
import os

from yaku.compat.rename \
    import \
        rename

def ensure_dir(path):
    dirname = os.path.dirname(path)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)

re_inc = re.compile(\
    '^[ \t]*(#|%:)[ \t]*(include)[ \t]*(.*)\r*$',
    re.IGNORECASE | re.MULTILINE)


RE_INCLUDE = re.compile('^\s*(<(?P<a>.*)>|"(?P<b>.*)")')

re_nl = re.compile('\\\\\r*\n', re.MULTILINE)
re_cpp = re.compile(\
    r"""(/\*[^*]*\*+([^/*][^*]*\*+)*/)|//[^\n]*|("(\\.|[^"\\])*"|'(\\.|[^'\\])*'|.[^/"'\\]*)""",
    re.MULTILINE)

def repl(m):
    s = m.group(1)
    if s is not None: return ' '
    s = m.group(3)
    if s is None: return ''
    return s

def extract_include(txt, defs):
    """process a line in the form "#include foo" to return a string representing the file"""
    m = RE_INCLUDE.search(txt)
    if m:
        if m.group('a'):
            return '<', m.group('a')
        if m.group('b'):
            return '"', m.group('b')

    return None, None

def lines_includes(filename):
    code = open(filename).read()
    #if use_trigraphs:
    #   for (a, b) in trig_def: code = code.split(a).join(b)
    code = re_nl.sub('', code)
    code = re_cpp.sub(repl, code)
    return [(m.group(2), m.group(3)) for m in re.finditer(re_inc, code)]

def find_deps(node, cpppaths=["/usr/include", "."]):
    nodes = []
    names = []

    def _find_deps(node):
        lst = lines_includes(node)

        for (_, line) in lst:
            t, filename = extract_include(line, None)
            if t is None:
                continue
            if filename in names:
                continue

            found = None
            for n in cpppaths:
                if found:
                    break
                if os.path.exists(os.path.join(n, filename)):
                    found = os.path.join(n, filename)
                #else:
                #    # XXX: most likely wrong
                #    found = os.path.join(n, filename)
                #    nodes.append(found)

            if not found:
                if not filename in names:
                    names.append(filename)
            elif not found in nodes:
                nodes.append(found)
                _find_deps(found)

    _find_deps(node)
    return nodes

def find_program(program, path_list=None):
    if path_list is None:
        path_list = os.environ["PATH"].split(os.pathsep)

    for p in path_list:
        ppath = os.path.join(p, program)
        if sys.platform == "win32":
            for ext in [".exe"]:
                epath = ppath + ext
                if os.path.exists(epath):
                    return epath
        else:
            if os.path.exists(ppath):
                return ppath

    return None
