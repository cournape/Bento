import sys
import ast

indent_width = 2

class NextParser(Exception): pass

class ParseError(Exception): pass

def strip_indents(data):
    lines = [l.rstrip() for l in data]
    cur_indent = 0
    out = []
    for l in lines:
        if l.strip():
            first_char = l.lstrip()[0]
            if first_char in ['"', "'", "#"]:
                continue

            # If line is not a comment or a string, parse
            # its indentation
            indent = (len(l) - len(l.lstrip())) / indent_width - cur_indent
            if indent > 0:
                out.extend(["{"] * indent)
            elif indent < 0:
                out.extend(["}"] * -indent)

            cur_indent += indent

        out.append(l.lstrip())

    out.extend(["}"] * cur_indent)

    return out

class Reader(object):
    def __init__(self, data):
        self._data = data
        self._idx = 0
        self.last_op = None

    def flush_empty(self):
        while not (self.eof() or self._data[self._idx].strip()):
            self._idx += 1

    def pop(self):
        if self.eof():
            return ''

        self.flush_empty()
        self._idx += 1
        self.last_op = 'pop'
        return self._data[self._idx - 1]

    def peek(self):
        if self.eof():
            return ''

        self.flush_empty()
        return self._data[self._idx]
        self.last_op = 'peek'

    def eof(self):
        return self._idx >= len(self._data)

    @property
    def index(self):
        return self._idx

    @property
    def line(self):
        lines = 0
        for l in self._data[:self._idx+1]:
            if not l in ['{', '}']:
                lines += 1
        return lines

    def parse_error(self, msg):
        raise ParseError('\n\nParsing error at line %s (%s):\n%s' %
                         (self.line, msg, self._data[self._idx]))

    def expect(self, sym, err):
        if not self.pop() == sym:
            self.parse_error(err)

    def parse(self, parsers, store=None, opt_arg=None):
        if self.eof():
            return

        try:
            parsers = list(parsers)
        except:
            parsers = list([parsers])

        index_before = self.index
        for p in parsers:
            try:
                if store is not None:
                    p(self, store, opt_arg)
                else:
                    p(self, opt_arg)
            except NextParser:
                pass
            else:
                assert self.index > index_before
                return True

        self.parse_error("No matching parser found for this line")

    def wait_for(self, sym):
        if self.eof():
            return False
        elif self.peek() != sym:
            return True
        else:
            return False

# --- expression functions ------------------------------------------------

def flag(foo):
    return bool(foo)

def os(name):
    return platform.platform().lower() == name

def arch(name):
    return platform.machine() == name

def impl(comparison):
    return bool(comparison)

class VersionCompare(object):
    def __init__(self, ver):
        self._ver = self.parse_ver(ver)

    def parse_ver(self, ver):
        if not isinstance(ver, tuple):
            ver = ver.split('.')
        ver = [int(v) for v in ver]
        return ver

    def __cmp__(self, ver):
        new_ver = self.parse_ver(ver)
        if new_ver == self._ver:
            return 0
        elif self._ver > self.parse_ver(ver):
            return 1
        else:
            return -1

expr_funcs = {'flag': flag,
              'os': os,
              'arch': arch,
              'impl': impl}

expr_constants = {'darwin': 'darwin',
                  'linux': 'linux',
                  'windows': 'windows',
                  'java': 'java',

                  'i386': 'i386',
                  'i686': 'i686',

                  'python': VersionCompare(sys.version_info[:3]),

                  'true': True,
                  'false': False}

# --- parsers start -------------------------------------------------------

def key_value(r, store, opt_arg=None):
    line = r.peek()
    if not ':' in line:
        raise NextParser

    l = r.pop()
    fields = l.split(':')
    if not len(fields) >= 2:
        r.parse_error('Invalid key-value pair')

    if ' ' in fields[0]:
        r.parse_error('Key-value cannot contain spaces.')

    store[fields[0]] = ' '.join(fields[1:]).strip()

def open_brace(r, opt_arg=None):
    r.expect('{', 'Expected indentation')

def close_brace(r, opt_arg=None):
    r.expect('}', 'Expected de-indentation')

def section(r, store, flags={}):
    section_header = r.peek()
    section_header = section_header.split()
    if len(section_header) < 1: raise NextParser
    if not section_header[0] in ['Flag', 'Library', 'Executable']:
        raise NextParser

    r.pop()
    if not len(section_header) == 2:
        r.parse_error('Invalid section header')

    section = section_header[0]
    name = section_header[1]

    if not section in store:
        store[section] = {}

    store[section][name] = {}
    store = store[section][name]

    r.parse(open_brace)

    while r.wait_for('}'):
        r.parse((key_value, if_statement), store, opt_arg=flags)

    r.parse(close_brace)

def if_statement(r, store, flags={}):
    if not r.peek().startswith('if '):
        raise NextParser

    expr = r.pop().lstrip('if').strip()
    expr_ast = ast.parse(expr, mode='eval')
    code = compile(expr_ast, filename=expr, mode='eval')
    expr_constants.update(flags)
    eval(code, expr_funcs, expr_constants)

    r.parse(open_brace)
    while r.wait_for('}'):
        r.parse(key_value, store)
    r.parse(close_brace)

    if r.peek() != 'else':
        return

    r.pop()
    while r.wait_for('}'):
        r.pop()

    r.parse(close_brace)


# --- parsers end -------------------------------------------------------

def get_flags(store, user_flags={}):
    flag_defines = store.get('Flag', {})
    flags = {}
    print store
    for flag_name, flag_attr in flag_defines.items():
        if flag_attr.get('Default') is not None:
            flags[flag_name.lower()] = bool(flag_attr['Default'])

    flags.update(user_flags)
    return flags

def parse(data, user_flags={}):
    data = strip_indents(data)
    r = Reader(data)

    info = {}

    while not r.eof():
        r.parse([key_value, section], store=info,
                                      opt_arg=get_flags(info, user_flags))

    return info

if __name__ == "__main__":
    f = open(sys.argv[1], 'r')
    data = f.readlines()
    print parse(data, {'webfrontend': True})
