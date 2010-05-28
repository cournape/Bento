import shlex

class CommaListLexer(object):
    def __init__(self, instream=None):
        if instream is not None:
            self._lexer = shlex.shlex(instream, posix=True)
        else:
            self._lexer = shlex.shlex(posix=True)
        self._lexer.whitespace += ','
        self._lexer.wordchars += './()*-$'
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

