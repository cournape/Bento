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
        return self.parser.parse(data, lexer=self.lexer, debug=debug)

def parse(data, debug=False):
    parser = Parser()
    return parser.parse(data, debug)

#-------------
#   Grammar
#-------------
def p_stmt_list(p):
    """stmt_list : stmt_list stmt"""
    p[0] = p[1]
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
    """meta_stmt : meta_name_stmt
                 | meta_summary_stmt
                 | meta_version_stmt
                 | meta_url_stmt
                 | meta_author_stmt
                 | meta_author_email_stmt
                 | meta_maintainer_stmt
                 | meta_maintainer_email_stmt
                 | meta_license_stmt
                 | meta_platforms_stmt
                 | meta_classifiers_stmt
    """
    p[0] = p[1]

def p_meta_name_stmt(p):
    """meta_name_stmt : NAME_ID COLON WORD
    """
    p[0] = Node("name", value=p[3])

def p_meta_summary_stmt(p):
    """meta_summary_stmt : SUMMARY_ID COLON single_line
    """
    p[0] = Node("summary", value=p[3])

def p_meta_url_stmt(p):
    """meta_url_stmt : URL_ID COLON anyword
    """
    p[0] = Node("url", value=p[3].value)

def p_meta_author_stmt(p):
    """meta_author_stmt : AUTHOR_ID COLON anyword
    """
    p[0] = Node("author", value=p[3].value)

def p_meta_author_email_stmt(p):
    """meta_author_email_stmt : AUTHOR_EMAIL_ID COLON anyword
    """
    p[0] = Node("author_email", value=p[3].value)

def p_meta_maintainer_stmt(p):
    """meta_maintainer_stmt : MAINTAINER_ID COLON anyword
    """
    p[0] = Node("maintainer", value=p[3].value)

def p_meta_maintainer_email_stmt(p):
    """meta_maintainer_email_stmt : MAINTAINER_EMAIL_ID COLON anyword
    """
    p[0] = Node("maintainer_email", value=p[3].value)

def p_meta_license_stmt(p):
    """meta_license_stmt : LICENSE_ID COLON anyword
    """
    p[0] = Node("license", value=p[3].value)

def p_meta_platforms_stmt(p):
    """meta_platforms_stmt : PLATFORMS_ID COLON anyword
    """
    p[0] = Node("platforms", value=p[3].value)

def p_meta_version_stmt(p):
    """meta_version_stmt : VERSION_ID COLON version
    """
    p[0] = Node("version", children=[p[3]])

def p_meta_classifiers_stmt_single_line(p):
    """meta_classifiers_stmt : CLASSIFIERS_ID COLON classifier"""
    p[0] = Node("classifiers", children=[p[3]])

def p_meta_classifiers_stmt_indent(p):
    """meta_classifiers_stmt : CLASSIFIERS_ID COLON NEWLINE INDENT classifiers_list DEDENT
    """
    p[0] = Node("classifiers", children=[p[5]])

def p_meta_classifiers_stmt(p):
    """meta_classifiers_stmt : CLASSIFIERS_ID COLON classifier NEWLINE INDENT classifiers_list DEDENT
    """
    p[0] = Node("classifiers", children=[p[3], p[6]])

def p_classifiers_list(p):
    """classifiers_list : classifier NEWLINE classifiers_list
    """
    p[0] = p[3]
    p[0].children.insert(0, p[1])

def p_classifiers_list_term(p):
    """classifiers_list : classifier
    """
    p[0] = Node("classifiers_list", children=[p[1]])

def p_classifier(p):
    """classifier : literal_line"""
    p[0] = p[1]
    p[0].value = "".join(p[0].value)
    p[0].type = "classifier"

#-----------------------
#   Literal handling
#-----------------------

# We produce a flat list here to speed things up (should do the same for
# description field)
def p_literal_line(p):
    """literal_line : anytoken literal_line"""
    p[0] = p[2]
    p[2].value.insert(0, p[1].value)

def p_literal_line_term(p):
    """literal_line : anytoken"""
    p[0] = Node("literal_line", value=[p[1].value])

def p_single_line_string(p):
    """single_line : single_line literal"""
    p[0] = p[1] + [p[2]]

def p_literal(p):
    """literal : WS 
               | WORD
               | DOT
    """
    p[0] = Node("literal", value=p[1])

def p_single_line_string_term(p):
    """single_line : literal"""
    p[0] = [p[1]]

# anyword groks any character stream without space|newline
def p_anyword(p):
    """anyword : anyword anytoken 
             | anytoken
    """
    if len(p) == 3:
        p[0] = Node("anyword", value=(p[1].value + p[2].value))
    elif len(p) == 2:
        p[0] = p[1]
    else:
        raise ValueError()

# Any token but whitespace, newline and comma
def p_anytoken_no_comma(p):
    """anytoken_no_comma : WORD
                         | INT
                         | DOT
                         | COLON
                         | LPAR
                         | RPAR
                         | DQUOTE
                         | STAR
                         | BQUOTE
                         | SQUOTE
                         | LESS
                         | SLASH
                         | SHARP
                         | EQUAL
                         | GREATER
                         | TILDE
                         | LBRACE
                         | RBRACE
                         | PERCENT
                         | AROBASE
                         | DOLLAR
                         | MINUS
    """
    p[0] = Node("anytoken", value=p[1])

# Any token but newline
def p_anytoken(p):
    """anytoken : anytoken_no_comma
    """
    p[0] = Node("anytoken", value=p[1].value)

def p_anytoken_term(p):
    """anytoken : COMMA
                | WS
    """
    p[0] = Node("anytoken", value=p[1])

def p_version(p):
    """version : num_part"""
    p[0] = p[1]

def p_num_part(p):
    """num_part : int DOT num_part
                | int
    """
    if len(p) == 4:
        p[0] = Node("num_part", children=[p[1]])
        p[0].children.append(p[3])
    elif len(p) == 2:
        p[0] = p[1]
    else:
        raise ValueError("YO")

def p_int(p):
    """int : INT"""
    value = int(p[1])
    p[0] = Node("int", value=value)
