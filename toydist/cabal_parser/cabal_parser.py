import os.path
import sys
import ast
import re
import platform
import shlex

from toydist.cabal_parser.items import \
        PathOption, FlagOption

indent_width = 4
header_titles = ['flag', 'library', 'executable', 'extension', 'path',
                 'datafiles']
list_fields = ['sources', 'packages', 'modules', 'buildrequires', 'platforms']
path_fields = ['sources', 'default', 'target']

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
        self._traceback = ['root']

    def flush_empty(self):
        """Read until a non-empty line is found."""
        while not (self.eof() or self._data[self._idx].strip()):
            self._idx += 1

    def pop(self, blank=False):
        """Return the next non-empty line and increment the line
        counter.  If `blank` is True, then also return blank lines.

        """
        if not blank:
            # Skip to the next non-empty line if blank is not set
            self.flush_empty()

        line = self.peek(blank)
        self._idx += 1

        return line

    def peek(self, blank=False):
        """Return the next non-empty line without incrementing the
        line counter.  If `blank` is True, also return blank lines.

        Peek is not allowed to touch _idx.

        """
        if self.eof():
            return ''

        save_idx = self._idx
        if not blank:
            self.flush_empty()

        peek_line = self._data[self._idx]
        self._idx = save_idx

        return peek_line

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
        raise ParseError('''

Parsing error at line %s (%s):
%s
Parser traceback: %s''' %
                         (self.line, msg, self._original_data[self.line],
                          ' -> '.join(self._traceback)))

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
            self._traceback.append(p.func_name)
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
            finally:
                self._traceback.pop()

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

def os_var(name):
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
              'os': os_var,
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

class CommaListLexer(object):
    def __init__(self, instream=None):
        if instream is not None:
            self._lexer = shlex.shlex(instream, posix=True)
        else:
            self._lexer = shlex.shlex(posix=True)
        self._lexer.whitespace += ','
        self._lexer.wordchars += './()*-'
        self.eof = self._lexer.eof

    def get_token(self):
        return self._lexer.get_token()

def comma_list_split(str):
    lexer = CommaListLexer(str)
    ret = []
    t = lexer.get_token()
    while t != lexer.eof:
        ret.append(t)
        t = lexer.get_token()

    return ret

def key_value(r, store, opt_arg=None):
    line = r.peek()
    if not ':' in line:
        raise NextParser

    if line.split(':')[0].lower() in header_titles:
        raise NextParser

    l = r.pop()
    fields = l.split(':')
    if not len(fields) >= 2:
        r.parse_error('invalid key-value pair')

    if ' ' in fields[0]:
        r.parse_error('key-value cannot contain spaces')

    # Allow flexible text indentation
    key = fields[0].lower()
    long_str_indentation = 0
    while r.peek() == '{':
        r.parse(open_brace)
        long_str_indentation += 1

    value = fields[1]
    for i in range(long_str_indentation):
        while r.wait_for('}'):
            this_line = r.pop(blank=True)
            if not this_line.strip():
                value += '\n\n'
            else:
                value += this_line + ' '
        r.parse(close_brace)

    value = value.strip()

    # Packages and modules are lists, handle them specially
    if key in list_fields:
        value = comma_list_split(value)

    # Handle path(path_variable). Ugly
    if key in path_fields:
        if opt_arg:
            paths = opt_arg.get('paths')
        else:
            paths = {}

    # If the key exists, append the new value, otherwise
    # create a new key-value pair
    if store.has_key(key):
        if key in list_fields:
            store[key].extend(value)
        else:
            raise ParseError("Double entry '%s' (old: %s, new: %s)" % \
                             (key, store[key], value))
    else:
        store[key] = value

def open_brace(r, opt_arg=None):
    r.expect('{', 'Expected indentation to increase')

def close_brace(r, opt_arg=None):
    r.expect('}', 'Expected indentation to decrease')

def _parse_section_header(r, line):
    header = [s.strip() for s in line.split(':')]
    if not len(header) == 2:
        r.parse_error("Invalid section header")
    type = header[0].lower()
    return header, type, header[1]

def section(r, store, flags={}):
    section_header = r.peek()
    if section_header.count(':') < 1: raise NextParser

    section_header, type, name = _parse_section_header(r, section_header)
    if not type in header_titles:
        raise NextParser
    elif type in ['path', 'flag', 'datafiles']:
        raise NextParser

    r.pop()
    if not len(section_header) == 2:
        r.parse_error('Invalid section header')

    if not type in store:
        store[type] = {}

    store[type][name] = {}
    store = store[type][name]

    r.parse(open_brace)

    while r.wait_for('}'):
        r.parse((if_statement, section, key_value), store, opt_arg=flags)
    r.parse(close_brace)

def datafiles_parser(r, store, flags={}):
    line = r.peek()

    section_header, type, name = _parse_section_header(r, line)
    if not type == 'datafiles':
        raise NextParser

    line = r.pop()

    if not store.has_key("datafiles"):
        store["datafiles"] = {}
    elif store['datafiles'].has_key(name):
        raise ParseError("DataFiles section %s already defined" % name)

    d_store = {}
    r.parse(open_brace)
    while r.wait_for('}'):
        r.parse((if_statement, key_value), d_store, opt_arg=flags)
    r.parse(close_brace)

    try:
        source = d_store['source']
    except KeyError:
        source = "."

    try:
        target = d_store['target']
    except KeyError:
        target = "$sitedir"

    try:
        files = comma_list_split(d_store['files'])
    except KeyError:
        files = []

    store["datafiles"][name] = {
        "source": source,
        "target": target,
        "files": files
    }

def path_parser(r, store, flags={}):
    line = r.peek()

    section_header, type, name = _parse_section_header(r, line)
    if not type == 'path':
        raise NextParser

    line = r.pop()
    for key in ['path', 'path_options']:
        if not key in store:
            store[key] = {}

    if store['path_options'].has_key(name):
        raise ParseError("Path %s already defined" % name)

    p_store = {}
    r.parse(open_brace)
    while r.wait_for('}'):
        r.parse((if_statement, key_value), p_store, opt_arg=flags)
    r.parse(close_brace)

    try:
        default = p_store['default']
    except KeyError:
        raise ParseError("Path %s has not default value" % name)

    try:
        descr = p_store['description']
    except KeyError:
        descr = None

    store['path'][name] = default
    store['path_options'][name] = PathOption(name, default, descr)

def flag_parser(r, store, flags={}):
    line = r.peek()

    section_header, type, name = _parse_section_header(r, line)
    if not type == 'flag':
        raise NextParser

    line = r.pop()
    for key in ['flag', 'flag_options']:
        if not key in store:
            store[key] = {}

    if store['flag_options'].has_key(name):
        raise ParseError("Flag %s already defined" % name)

    f_store = {}
    r.parse(open_brace)
    while r.wait_for('}'):
        r.parse((if_statement, key_value), f_store, opt_arg=flags)
    r.parse(close_brace)

    try:
        default = f_store['default']
    except KeyError:
        raise ParseError("Flag %s has not default value" % name)

    try:
        descr = f_store['description']
    except KeyError:
        descr = None

    store['flag'][name] = default
    store['flag_options'][name] = FlagOption(name, default, descr)

def eval_statement(expr, vars):
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
    expr_constants.update(vars['flags'])
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
    flag_options = store.get('flag_options', {})
    for name, flag in flag_options.items():
        user_flags[name] = flag.default_value
    return user_flags

def get_flag_options(store):
    return store.get('flag_options', {})

def get_paths(store, user_paths={}):
    """Given the variables returned by the parser, return the paths found. If
    `user_paths` are provided, these override those found during parsing.
    """
    path_options = store.get('path_options', {})
    for name, path in path_options.items():
        user_paths[name] = path.default_value
    return user_paths

def get_path_options(store):
    return store.get('path_options', {})

def parse(data, user_flags={}, user_paths={}):
    """Given lines from a config file, parse them.  `user_flags` may
    optionally be given to override any flags found in the config
    file.

    """
    r = Reader(data)

    info = {}

    while not r.eof():
        r.parse([key_value, section, datafiles_parser, path_parser, flag_parser], store=info,
                opt_arg={'flags': get_flags(info, user_flags),
                         'flag_options': get_flag_options(info),
                         'path_options': get_path_options(info),
                         'paths': get_paths(info, user_paths)})

    return info

if __name__ == "__main__":
    import textwrap

    def print_dict(d, indent=0):
        for (key, value) in d.items():
            indent_str = indent * ' '
            if isinstance(value, dict):
                if key.strip():
                    print '%s%s:' % (indent_str, key)
                print_dict(value, indent=indent + indent_width)
            else:
                out = indent_str + '%s: %s' % (key, value)
                print out
                #if len(out) > 78:
                #    print '%s:' % key
                #    wrap = '\n\n'.join(
                #        [textwrap.fill(par, 78 - indent - indent_width)
                #         for par in value.split('\n\n')])
                #    for l in wrap.split('\n'):
                #        print indent_str + indent_width*' ' + l
                #else:
                #    print out

    # TODO: implement simple variable interpolation for default user_paths
    user_paths = {
            'prefix': '/usr/local',
            'eprefix': '/usr/local',
            'bindir': '/usr/local/bin',
            'libdir': '/usr/local/lib',
            'includedir': '/usr/local/include',
            'datarootdir': '/usr/local/share',
            'datadir': '/usr/local/share',
            'mandir': '/usr/local/share/man',
    }
    f = open(sys.argv[1], 'r')
    data = f.readlines()
    meta_data = parse(data, {'webfrontend': True}, user_paths)

    print_dict(meta_data)
