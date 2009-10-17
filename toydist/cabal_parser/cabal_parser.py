indent_width = 2

class NextParser(Exception): pass

class ParseError(Exception): pass

def strip_indents(data):
    lines = [l.rstrip() for l in data]
    indent = 0
    out = []
    for l in lines:
        if l.strip():
            first_char = l.lstrip()[0]
            if first_char in ['"', "'", "#"]:
                continue

            # If line is not a comment or a string, parse
            # its indentation
            indentation = len(l) - len(l.lstrip())
            if indentation == indent_width * (indent + 1):
                out.append("{")
                indent += 1
            elif indentation == indent_width * (indent - 1):
                indent -= 1
                out.append("}")

        out.append(l.lstrip())

    if indent > 0:
        out.append("}")

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

    def parse(self, parsers, store=None):
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
                    p(self, store=store)
                else:
                    p(self)
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

# --- parsers start -------------------------------------------------------

def key_value(r, store):
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

def open_brace(r):
    r.expect('{', 'Expected indentation')

def close_brace(r):
    r.expect('}', 'Expected de-indentation')

def section(r, store):
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
        r.parse((key_value, if_statement), store)

    r.parse(close_brace)

def if_statement(r, store):
    if not r.peek().startswith('if '):
        raise NextParser

    r.pop()
    r.parse(open_brace)
    while r.wait_for('}'):
        r.pop()
    r.parse(close_brace)

    if r.peek() != 'else':
        return

    r.pop()
    while r.wait_for('}'):
        r.pop()

    r.parse(close_brace)


# --- parsers end -------------------------------------------------------


def parse(data):
    data = strip_indents(data)
    r = Reader(data)

    info = {}

    while not r.eof():
        r.parse([key_value, section], store=info)

    return info

if __name__ == "__main__":
    import sys
    f = open(sys.argv[1], 'r')
    data = f.readlines()
    print parse(data)
