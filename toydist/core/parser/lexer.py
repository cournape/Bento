import ply
import ply.lex

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
