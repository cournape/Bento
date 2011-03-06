class ParseError(Exception):
    def __init__(self, msg, token):
        self.msg = msg
        self.lineno = token.lineno
        self.tp = token.type
        self.value = token.value
        self.token = token
        self.filename = None
        Exception.__init__(self, msg)

    def __str__(self):
        if self.filename is None:
            return Exception.__str__(self)
        else:
            msg = '  File "%(file)s", line %(lineno)d\n' \
                  % {"file": self.filename, "lineno": self.lineno}
            f = open(self.filename)
            try:
                # This is expensive, there must be a better way
                cnt = f.read()
                lines = cnt.splitlines()
                linepos = sum([(len(l)+1) for l in lines[:self.lineno-1]])
                msg += "%s\n" % lines[self.lineno-1]
                pos = self.token.lexpos
                msg += " " * (pos - linepos) + "^\n"
                msg += "Syntax error"
                return msg
            finally:
                f.close()

    def __repr__(self):
        return self.__str__()
