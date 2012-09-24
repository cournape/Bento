import sys
import errno

import os.path as op

import ply.yacc

import bento.parser.rules

from bento._config \
    import \
        _PICKLED_PARSETAB, _OPTIMIZE_LEX, _DEBUG_YACC
from bento.utils.utils \
    import \
        extract_exception
from bento.errors \
    import \
        InternalBentoError, BentoError, ParseError
from bento.parser.lexer \
    import \
        BentoLexer, tokens as _tokens

# XXX: is there a less ugly way to do this ?
__GLOBALS = globals()
for k in dir(bento.parser.rules):
    if k.startswith("p_"):
        __GLOBALS[k] = getattr(bento.parser.rules, k)

# Do not remove: this is used by PLY
tokens = [t for t in _tokens if not t in ["WS", "NEWLINE", "BACKSLASH"]]

def _has_parser_changed(picklefile):
    # FIXME: private function to determine whether ply will need to write to
    # the pickled grammar file. Highly implementation dependent.
    from ply.yacc import PlyLogger, get_caller_module_dict, ParserReflect, YaccError, LRTable
    errorlog = PlyLogger(sys.stderr)

    pdict = get_caller_module_dict(2)

    # Collect parser information from the dictionary
    pinfo = ParserReflect(pdict, log=errorlog)
    pinfo.get_all()

    if pinfo.error:
        raise YaccError("Unable to build parser")

    # Check signature against table files (if any)
    signature = pinfo.signature()

    # Read the tables
    try:
        lr = LRTable()
        read_signature = lr.read_pickle(picklefile)
        return read_signature != signature
    except Exception:
        return True

class Parser(object):
    def __init__(self, lexer=None):
        if lexer is None:
            self.lexer = BentoLexer(optimize=_OPTIMIZE_LEX)
        else:
            self.lexer = lexer

        picklefile = _PICKLED_PARSETAB
        if not op.exists(picklefile):
            try:
                fid = open(picklefile, "wb")
                fid.close()
            except IOError:
                e = extract_exception()
                raise BentoError("Could not write pickle file %r (original error was %r)" % (picklefile, e))
        else:
            try:
                fid = open(_PICKLED_PARSETAB, "wb")
                fid.close()
            except IOError:
                # In case of read-only support (no write access, zip import,
                # etc...)
                e = extract_exception()
                if e.errno == errno.EACCES:
                    if _has_parser_changed(_PICKLED_PARSETAB):
                        raise BentoError("Cannot write new updated grammar to file %r" % _PICKLED_PARSETAB)
                else:
                    raise
        self.parser = ply.yacc.yacc(start="stmt_list",
                                picklefile=picklefile,
                                debug=_DEBUG_YACC)

    def parse(self, data):
        res = self.parser.parse(data, lexer=self.lexer)
        ## FIXME: this is stupid, deal correctly with empty ast in the grammar proper
        #if res is None:
        #    res = Node("empty")
        return res

    def reset(self):
        # XXX: implements reset for lexer
        self.lexer = BentoLexer(optimize=_OPTIMIZE_LEX)
        # XXX: ply parser.reset method expects those attributes to
        # exist
        self.parser.statestack = []
        self.parser.symstack = []
        return self.parser.restart()

__PARSER = None
def parse(data):
    global __PARSER
    if __PARSER is None:
        __PARSER = Parser()
    else:
        __PARSER.reset()
    return __PARSER.parse(data)
    #return Parser().parse(data)

def p_error(p):
    if p is None:
        raise InternalBentoError("Unknown parsing error (parser/lexer bug ? Please report this with your bento.info)")
    else:
        msg = "yacc: Syntax error at line %d, Token(%s, %r)" % \
                (p.lineno, p.type, p.value)
        if hasattr(p.lexer, "lexdata"):
            data = p.lexer.lexdata.splitlines()
            msg += "\n\t%r" % (data[p.lineno-1],)
        raise ParseError(msg, p)
