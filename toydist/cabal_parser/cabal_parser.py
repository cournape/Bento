import sys
import ast
import re
import platform

indent_width = 4
header_titles = ['Flag', 'Library', 'Executable', 'Extension']

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
        self._data = strip_indents(data)
        self._original_data = data
        self._idx = 0

    def flush_empty(self):
        """Read until a non-empty line is found."""
        while not (self.eof() or self._data[self._idx].strip()):
            self._idx += 1

    def pop(self):
        """Return the next non-empty line and increment the line counter."""
        line = self.peek()
        self._idx += 1
        return line

    def peek(self):
        """Return the next non-empty line without incrementing the
        line counter.

        """
        if self.eof():
            return ''

        self.flush_empty()
        return self._data[self._idx]

    def eof(self):
        """Return True if the end of the file has been reached."""
        return self._idx >= len(self._data)

    @property
    def index(self):
        """Return the line-counter to the pre-processed version of
        the input file.

        """
        return self._idx

    @property
    def line(self):
        """Return the line-counter to the original input file.

        """
        lines = 0
        for l in self._data[:self._idx]:
            if not l in ['{', '}']:
                lines += 1
        return lines

    def parse_error(self, msg):
        """Raise a parsing error with the given message."""
        raise ParseError('\n\nParsing error at line %s (%s):\n%s' %
                         (self.line, msg, self._original_data[self.line]))

    def expect(self, line, err):
        """Ensure that the next line equals `line`.

        """
        if not self.pop() == line:
            self.parse_error(err)

    def parse(self, parsers, store=None, opt_arg=None):
        """Given one or more parser functions, use these to parse the
        next line.  The dict `store` is provided as an argument to the
        parser, and is mainly used to store key-value pairs generated
        while parsing.  `opt_arg` is an optional argument to the parser.

        """
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

        if self.peek() in ['{', '}']:
            self.parse_error("Unexpected indentation")

        self.parse_error("No matching parser found for this line")

    def wait_for(self, line):
        """Keep reading until the given line has been seen."""
        if self.eof():
            return False
        elif self.peek() != line:
            return True
        else:
            return False

# --- expression functions ------------------------------------------------

def flag(foo):
    return bool(foo)

def os(name):
    return platform.system().lower() == name

def arch(name):
    return platform.machine() == name

def impl(comparison):
    return bool(comparison)

class VersionCompare(object):
    """Compare version strings, e.g., 2.6.1 >= 2.6.0.

    """
    def __init__(self, ver):
        self._ver = self._parse_ver(ver)

    def _parse_ver(self, ver):
        if not isinstance(ver, tuple):
            ver = ver.split('.')
        ver = [int(v) for v in ver]
        return ver

    def __cmp__(self, ver):
        """Provide the comparison operators."""
        new_ver = self._parse_ver(ver)
        if new_ver == self._ver:
            return 0
        elif self._ver > self._parse_ver(ver):
            return 1
        else:
            return -1

expr_funcs = {'flag': flag,
              'os': os,
              'arch': arch,
              'impl': impl}

expr_constants = {'darwin': 'darwin',
                  'macosx': 'darwin',
                  'linux': 'linux',
                  'windows': 'windows',
                  'java': 'java',

                  'i386': 'i386',
                  'i686': 'i686',

                  'python': VersionCompare(sys.version_info[:3]),

                  'true': True,
                  'false': False}

# --- parsers start -------------------------------------------------------

# Refer to http://www.haskell.org/cabal/release/cabal-latest/doc/users-guide/

def key_value(r, store, opt_arg=None):
    line = r.peek()
    if not ':' in line:
        raise NextParser

    if line.split(':')[0] in header_titles:
        raise NextParser

    l = r.pop()
    fields = l.split(':')
    if not len(fields) >= 2:
        r.parse_error('invalid key-value pair')

    if ' ' in fields[0]:
        r.parse_error('key-value cannot contain spaces')

    key = fields[0]
    if r.peek() == '{':
        r.parse(open_brace)
        value = []
        while r.wait_for('}'):
            value.append(r.pop())
        value = ' '.join(value)
        r.parse(close_brace)
    else:
        value = ' '.join(fields[1:]).strip()

    # Packages and modules are lists, handle them specially
    if key in ['Packages', 'Modules']:
        value = [v.strip() for v in value.split(',')]

    # If the key exists, append the new value, otherwise
    # create a new key-value pair
    if store.has_key(key):
        if not isinstance(store[key], list):
            store[key] = [store[key], value]
        else:
            store[key].append(value)
    else:
        store[key] = value

def open_brace(r, opt_arg=None):
    r.expect('{', 'Expected indentation')

def close_brace(r, opt_arg=None):
    r.expect('}', 'Expected de-indentation')

def section(r, store, flags={}):
    section_header = r.peek()
    if section_header.count(':') < 1: raise NextParser

    section_header = [s.strip() for s in section_header.split(':')]
    if not section_header[0] in header_titles:
        raise NextParser

    r.pop()
    if not len(section_header) == 2:
        r.parse_error('Invalid section header')

    section_type = section_header[0]
    name = section_header[1]

    if not section_type in store:
        store[section_type] = {}

    store[section_type][name] = {}
    store = store[section_type][name]

    r.parse(open_brace)

    while r.wait_for('}'):
        r.parse((if_statement, section, key_value), store, opt_arg=flags)
    r.parse(close_brace)

def eval_statement(expr, flags):
    # replace version numbers with strings, e.g. 2.6.1 -> '2.6.1'
    ver_descr = re.compile('[^\'\."0-9](\d+\.)+\d+')
    match = ver_descr.search(expr)
    while match:
        start, end = match.start(), match.end()
        expr = expr[:start + 1] + '"' + expr[start + 1:end] + '"' + \
               expr[end:]
        match = ver_descr.match(expr)

    # Parse, compile and execute the expression
    expr_ast = ast.parse(expr, mode='eval')
    code = compile(expr_ast, filename=expr, mode='eval')
    expr_constants.update(flags)
    return eval(code, expr_funcs, expr_constants)

def if_statement(r, store, flags={}):
    if not r.peek().startswith('if '):
        raise NextParser

    expr = r.pop().lstrip('if').strip()
    expr_true = eval_statement(expr, flags)

    # Parse the contents of the if-statement
    r.parse(open_brace)
    while r.wait_for('}'):
        if expr_true:
            use_store = store
        else:
            use_store = {}

        r.parse((if_statement, section, key_value), use_store)

    r.parse(close_brace)

    if r.peek() != 'else':
        return

    r.pop()
    r.parse(open_brace)
    # Parse the else part of the statement
    while r.wait_for('}'):
        if expr_true:
            use_store = store
        else:
            use_store = {}

        r.parse((if_statement, section, key_value), use_store)

    r.parse(close_brace)


# --- parsers end -------------------------------------------------------

def get_flags(store, user_flags={}):
    """Given the variables returned by the parser, return the
    flags found.  If `user_flags` are provided, these override those
    found during parsing.

    """
    flag_defines = store.get('Flag', {})
    flags = {}
    for flag_name, flag_attr in flag_defines.items():
        if flag_attr.get('Default') is not None:
            flags[flag_name.lower()] = bool(flag_attr['Default'])

    flags.update(user_flags)
    return flags

def parse(data, user_flags={}):
    """Given lines from a config file, parse them.  `user_flags` may
    optionally be given to override any flags found in the config
    file.

    """
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
