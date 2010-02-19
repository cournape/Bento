import ply
import ply.lex

from toydist.core.parser.utils \
    import \
        Peeker
__all__ = ["MyLexer"]

#==============
#   Lexer
#==============
tokens = ('COLON', 'DOT', 'INT', 'WS', 'NEWLINE', 'WORD', 'COMMA', 'SLASH',
          'BACKSLASH', 'LPAR', 'RPAR', 'DQUOTE', 'SQUOTE', 'STAR', 'LESS',
          'DOLLAR', 'TILDE', 'LBRACE', 'RBRACE', 'PERCENT', 'AROBASE',
          'GREATER', 'PLUS', 'EQUAL', 'MINUS', 'SHARP', 'BQUOTE', 'NAME_ID',
          'SUMMARY_ID', 'DESCRIPTION_ID', 'INDENT', 'DEDENT', 'LIBRARY_ID',
          'PACKAGES_ID', 'VERSION_ID', 'MODULES_ID', 'EXTENSION_ID',
          'SOURCES_ID', 'DATAFILES_ID', 'TARGET_ID', 'FILES_ID', 'SRCDIR_ID',
          'URL_ID', 'AUTHOR_ID', 'AUTHOR_EMAIL_ID', 'MAINTAINER_ID',
          'MAINTAINER_EMAIL_ID', 'LICENSE_ID', 'PLATFORMS_ID', 'CLASSIFIERS_ID',
          'PATH_ID', 'DEFAULT_ID', 'EXTRA_SOURCES_ID', 'EXECUTABLE_ID',
          'MODULE_ID', 'FUNCTION_ID')

# List of FIELD keywords -> Token TYPE inside PLY lexer
META_FIELDS_ID = {
    "Version": "VERSION_ID",
    "Summary": "SUMMARY_ID",
    "Description": "DESCRIPTION_ID",
    "Name": "NAME_ID",
    "DataFiles": "DATAFILES_ID",
    "Library": "LIBRARY_ID",
    "Packages": "PACKAGES_ID",
    "Modules": "MODULES_ID",
    "Extension": "EXTENSION_ID",
    "Sources": "SOURCES_ID",
    "TargetDir": "TARGET_ID",
    "Files": "FILES_ID",
    "SourceDir": "SRCDIR_ID",
    "Url": "URL_ID",
    "Author": "AUTHOR_ID",
    "AuthorEmail": "AUTHOR_EMAIL_ID",
    "Maintainer": "MAINTAINER_ID",
    "MaintainerEmail": "MAINTAINER_EMAIL_ID",
    "License": "LICENSE_ID",
    "Platforms": "PLATFORMS_ID",
    "Classifiers": "CLASSIFIERS_ID",
    "Path": "PATH_ID",
    "Default": "DEFAULT_ID",
    "ExtraSourceFiles": "EXTRA_SOURCES_ID",
    "Executable": "EXECUTABLE_ID",
    "Module": "MODULE_ID",
    "Function": "FUNCTION_ID",
}

# ID -> field type dict
FIELD_TYPE = {
    "NAME_ID": "WORD",
    "VERSION_ID": "WORDS",
    "SUMMARY_ID": "LINE",
    "DESCRIPTION_ID": "MULTILINE",
    "LIBRARY_ID": "WORD",
    "PACKAGES_ID": "WORDS",
    "MODULES_ID": "WORDS",
    "SOURCES_ID": "WORDS",
    "EXTENSION_ID": "WORD",
    "DATAFILES_ID": "WORD",
    "TARGET_ID": "WORDS",
    "SRCDIR_ID": "WORDS",
    "FILES_ID": "WORDS",
    "URL_ID": "WORDS",
    "AUTHOR_ID": "WORDS",
    "AUTHOR_EMAIL_ID": "WORDS",
    "MAINTAINER_ID": "WORDS",
    "MAINTAINER_EMAIL_ID": "WORDS",
    "LICENSE_ID": "WORDS",
    "PLATFORMS_ID": "WORDS",
    "CLASSIFIERS_ID": "MULTILINE",
    "PATH_ID": "WORD",
    "DEFAULT_ID": "WORDS",
    "EXTRA_SOURCES_ID": "WORDS",
    "EXECUTABLE_ID": "WORD",
    "MODULE_ID": "WORDS",
    "FUNCTION_ID": "WORDS",
}

t_COLON = r':'
t_DOT = r'\.'
t_INT = r'\d+'
t_COMMA = r','
t_SLASH = r"\/"
t_BACKSLASH = r"\\"
t_LPAR = r"\("
t_RPAR = r"\)"
t_SQUOTE = r"'"
t_DQUOTE = r"\""
t_STAR = r"\*"
t_LESS = r"\<"
t_GREATER = r"\>"
t_PLUS = r"\+"
t_MINUS = r"-"
t_EQUAL = r"="
t_BQUOTE = r"`"
t_SHARP = r"\#"
t_DOLLAR = r"\$"
t_TILDE = r"~"
t_LBRACE = r"{"
t_RBRACE = r"}"
t_PERCENT = r"%"
t_AROBASE = r"@"

def t_WORD(t):
    # FIXME: how to handle special characters in "words", such as for paths
    # variables ?
    #r'[\/\\a-zA-Z_][\/\\\w]*'
    r'[a-zA-Z_][\w_-]*'
    return t

# Whitespace
def t_WS(t):
    r' [ ]+ '
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    t.type = "NEWLINE"
    return t

def t_error(t):
    msg = "Illegal character '%s' at line %d" % (t.value[0], t.lineno)
    raise SyntaxError(msg)

def t_tab(t):
    r'\t'
    msg = "Illegal tab character at line %d" % t.lineno
    raise SyntaxError(msg)

class MyLexer(object):
    def __init__(self, module=None, object=None, debug=0, optimize=0,
                 lextab='lextab', reflags=0, nowarn=0, outputdir='',
                 debuglog=None, errorlog=None):
        self.lexer = ply.lex.lex(module, object, debug, optimize, lextab,
                                 reflags, nowarn, outputdir, debuglog,
                                 errorlog)

    def input(self, *a, **kw):
        self.lexer.input(*a, **kw)
        self.token_stream = iter(self.lexer.token, None)

    def token(self, *a, **kw):
        try:
            return self.token_stream.next()
        except StopIteration:
            return None

def indent_generator(token_stream):
    """Post process the given stream of tokense to generate INDENT/DEDENT
    tokens.
    
    Note
    ----
    Each generated token's value is the total amount of spaces from the
    beginning of the line.
    
    The way indentation tokens are generated is similar to how it works in
    python."""
    stack = [0]

    # Dummy token to track the token just before the current one
    former = ply.lex.LexToken()
    former.type = "NEWLINE"
    former.value = "dummy"
    former.lineno = 0
    former.lexpos = -1

    sentinel = ply.lex.LexToken()
    sentinel.type = "LAST_TOKEN"
    sentinel.value = "dummy"
    sentinel.lineno = -1
    sentinel.lexpos = -1

    def generate_dedent(stck, tok):
        amount = stck.pop(0)
        return new_dedent(amount, tok)

    tokens = Peeker(token_stream, dummy=sentinel)

    for token in tokens:
        if former.type == "NEWLINE":
            if token.type == "WS":
                indent = len(token.value)
            else:
                indent = 0

            if indent == stack[0]:
                former = token
                if indent > 0:
                    token = tokens.next()
                    former = token
                    yield token
                else:
                    yield former
            elif indent > stack[0]:
                stack.insert(0, indent)
                ind = new_indent(indent, token)
                former = ind
                yield ind
            elif indent < stack[0]:
                if not indent in stack:
                    raise ValueError("Wrong indent at line %d" % token.lineno)
                while stack[0] > indent:
                    former = generate_dedent(stack, token)
                    yield former
                if stack[0] > 0:
                    former = tokens.next()
                    yield former
                else:
                    former = token
                    yield token
        else:
            former = token
            yield token

    # Generate additional DEDENT so that the number of INDENT/DEDENT always
    # match
    while len(stack) > 1:
        former = generate_dedent(stack, token)
        yield former

def new_indent(amount, token):
    tok = ply.lex.LexToken()
    tok.type = "INDENT"
    tok.value = amount
    tok.lineno = token.lineno
    tok.lexpos = token.lexpos
    return tok

def new_dedent(amount, token):
    tok = ply.lex.LexToken()
    tok.type = "DEDENT"
    tok.value = amount
    tok.lineno = token.lineno
    tok.lexpos = token.lexpos
    return tok

def _new_token(type, token):
    tok = ply.lex.LexToken()
    tok.type = type
    tok.value = token.value
    tok.lineno = token.lineno
    tok.lexpos = token.lexpos
    return tok
