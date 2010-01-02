class NextParser(Exception): pass

class ParseError(Exception): pass

class Reader(object):
    def __init__(self, data, original_data=None):
        self._data = data
        if original_data:
            self._original_data = original_data
        else:
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

Parsing error at line %s: %s:
    line is:
    %s
Parser traceback: %s''' %
                         (self.line, msg, self._original_data[self.line-1],
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

