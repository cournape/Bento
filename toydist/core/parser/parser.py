import sys
import ply
import ply.lex
import ply.yacc

from toydist.core.parser.lexer \
    import \
        MyLexer, tokens

from toydist.core.parser.nodes \
    import \
        Node

class Parser(object):
    def __init__(self, lexer=None):
        self.parser = ply.yacc.yacc(start="stmt_list")
        if lexer is None:
            self.lexer = MyLexer(stage=3)
        else:
            self.lexer = lexer

    def parse(self, data, debug=False):
        return self.parser.parse(data, lexer=self.lexer)

def parse(data, debug=False):
    parser = Parser()
    return parser.parse(data, debug)

#-------------
#   Grammar
#-------------
def p_stmt_list(p):
    """stmt_list : stmt_list stmt"""
    if p[1].type == "stmt_list":
        p[0] = p[1]
    else:
        p[0] = Node("stmt_list", children=[p[1]])
    if p[2].type not in ("newline",):
        p[0].children.append(p[2])

def p_stmt_list_term(p):
    """stmt_list : stmt"""
    p[0] = Node("stmt_list", children=[p[1]])

def p_stmt_list_empty(p):
    """stmt_list : empty"""
    pass

def p_stmt_list_newline(p):
    """stmt_list : NEWLINE"""
    pass

def p_stmt(p):
    """stmt : meta_stmt
    """
    p[0] = p[1]

def p_empty(p):
    """empty : """
    pass

#----------------
#   Meta data
#----------------
def p_meta_stmt(p):
    """meta_stmt : meta_name_stmt"""
    p[0] = p[1]

def p_meta_name_stmt(p):
    """meta_name_stmt : NAME_ID COLON WORD
    """
    p[0] = Node("name", value=p[3])
