from ply.lex \
    import \
        LexToken, lex

from bento.core.utils \
    import \
        gen_next
from bento.core.parser.utils \
    import \
        Peeker, BackwardGenerator
__all__ = ["MyLexer"]

#==============
#   Lexer
#==============
tokens = ('COLON', 'DOUBLE_COLON', 'WS', 'NEWLINE', 'WORD', 'COMMA', 'SLASH',
          'BACKSLASH', 'LPAR', 'RPAR', 'LESS',
          'GREATER', 'EQUAL', 'SHARP', 'NAME_ID', 'KEYWORDS_ID',
          'SUMMARY_ID', 'DESCRIPTION_ID', 'INDENT', 'DEDENT', 'LIBRARY_ID',
          'PACKAGES_ID', 'VERSION_ID', 'MODULES_ID', 'EXTENSION_ID',
          'COMPILED_LIBRARY_ID',
          'SOURCES_ID', 'DATAFILES_ID', 'TARGET_ID', 'FILES_ID', 'SRCDIR_ID',
          'URL_ID', 'AUTHOR_ID', 'AUTHOR_EMAIL_ID', 'MAINTAINER_ID',
          'MAINTAINER_EMAIL_ID', 'LICENSE_ID', 'PLATFORMS_ID', 'CLASSIFIERS_ID',
          'PATH_ID', 'DEFAULT_ID', 'EXTRA_SOURCE_FILES_ID', 'EXECUTABLE_ID',
          'FUNCTION_ID', 'MODULE_ID', 'FLAG_ID', 'INCLUDE_DIRS_ID',
          'IF', 'TRUE', 'FALSE', 'AND', 'OS_OP', 'ELSE', 'FLAG_OP',
          'BUILD_REQUIRES_ID', 'INSTALL_REQUIRES_ID',
          'DOWNLOAD_URL_ID', 'HOOK_FILE_ID', 'CONFIG_PY_ID', 'NOT_OP',
          'SUBENTO_ID', 'DESCRIPTION_FROM_FILE_ID', 'META_TEMPLATE_FILE_ID',
          'SUB_DIRECTORY_ID')

ESCAPING_CHAR = dict([(t, False) for t in tokens])
ESCAPING_CHAR["BACKSLASH"] = True

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
    "CompiledLibrary": "COMPILED_LIBRARY_ID",
    "Sources": "SOURCES_ID",
    "IncludeDirs": "INCLUDE_DIRS_ID",
    "TargetDir": "TARGET_ID",
    "Files": "FILES_ID",
    "SourceDir": "SRCDIR_ID",
    "Url": "URL_ID",
    "DownloadUrl": "DOWNLOAD_URL_ID",
    "Author": "AUTHOR_ID",
    "AuthorEmail": "AUTHOR_EMAIL_ID",
    "Maintainer": "MAINTAINER_ID",
    "MaintainerEmail": "MAINTAINER_EMAIL_ID",
    "License": "LICENSE_ID",
    "Platforms": "PLATFORMS_ID",
    "Classifiers": "CLASSIFIERS_ID",
    "Keywords": "KEYWORDS_ID",
    "Path": "PATH_ID",
    "Flag": "FLAG_ID",
    "Default": "DEFAULT_ID",
    "ExtraSourceFiles": "EXTRA_SOURCE_FILES_ID",
    "Executable": "EXECUTABLE_ID",
    "Function": "FUNCTION_ID",
    "Module": "MODULE_ID",
    "BuildRequires": "BUILD_REQUIRES_ID",
    "InstallRequires": "INSTALL_REQUIRES_ID",
    "HookFile": "HOOK_FILE_ID",
    "ConfigPy": "CONFIG_PY_ID",
    "Recurse": "SUBENTO_ID",
    "DescriptionFromFile": "DESCRIPTION_FROM_FILE_ID",
    "MetaTemplateFile": "META_TEMPLATE_FILE_ID",
    "SubDirectory": "SUB_DIRECTORY_ID",
}

CONDITIONAL_ID = {
    "if": "IF",
    "else": "ELSE",
    "true": "TRUE",
    "false": "FALSE",
    "and": "AND",
    "os": "OS_OP",
    "flag": "FLAG_OP",
    "not": "NOT_OP",
}

# ID -> field type dict
FIELD_TYPE = {
    "NAME_ID": "WORD",
    "VERSION_ID": "WORDS",
    "SUMMARY_ID": "LINE",
    "DESCRIPTION_ID": "MULTILINE",
    "DESCRIPTION_FROM_FILE_ID": "WORD",
    "LIBRARY_ID": "WORD",
    "PACKAGES_ID": "WORDS",
    "MODULES_ID": "WORDS",
    "SOURCES_ID": "WORDS",
    "EXTENSION_ID": "WORD",
    "COMPILED_LIBRARY_ID": "WORD",
    "INCLUDE_DIRS_ID": "WORD",
    "DATAFILES_ID": "WORD",
    "TARGET_ID": "WORDS",
    "SRCDIR_ID": "WORDS",
    "FILES_ID": "WORDS",
    "URL_ID": "WORDS",
    "DOWNLOAD_URL_ID": "WORDS",
    "AUTHOR_ID": "LINE",
    "AUTHOR_EMAIL_ID": "WORDS",
    "MAINTAINER_ID": "LINE",
    "MAINTAINER_EMAIL_ID": "WORDS",
    "LICENSE_ID": "WORDS",
    "PLATFORMS_ID": "WORDS",
    "CLASSIFIERS_ID": "COMMA_LIST",
    "PATH_ID": "WORD",
    "FLAG_ID": "WORD",
    "DEFAULT_ID": "WORDS",
    "EXTRA_SOURCE_FILES_ID": "WORDS",
    "EXECUTABLE_ID": "WORD",
    "FUNCTION_ID": "WORDS",
    "MODULE_ID": "WORD",
    "BUILD_REQUIRES_ID": "WORDS",
    "INSTALL_REQUIRES_ID": "WORDS",
    "HOOK_FILE_ID": "WORDS",
    "CONFIG_PY_ID": "WORD",
    "SUBENTO_ID": "WORDS",
    "META_TEMPLATE_FILE_ID": "WORD",
    "KEYWORDS_ID": "WORDS",
    "SUB_DIRECTORY_ID": "WORDS",
}

# Special characters: everytime one is added/changed, update t_WORD
# regex if necessary
t_DOUBLE_COLON = r'::'
t_COLON = r':'
t_COMMA = r','
t_SLASH = r"\/"
t_BACKSLASH = r"\\"
t_LPAR = r"\("
t_RPAR = r"\)"
t_LESS = r"\<"
t_GREATER = r"\>"
t_EQUAL = r"="
t_SHARP = r"\#"

def t_WORD(t):
    # Match everything but whitespace and special characters
    r'([^#^:^,^\s^\\^(^).]|[.])+'
    return t

# Whitespace
def t_WS(t):
    r' [ ]+ '
    return t

def t_newline(t):
    r'\n+|(\r\n)+'
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

class _Dummy(object):
    def __init__(self):
        self.type = "EOF"
        self.escaped = False
        self.value = None

    def __repr__(self):
        return "DummyToken(EOF)"

EOF = _Dummy()

class MyLexer(object):
    _stages = dict(zip(
        ('raw', 'escape_detected', 'escape_merged', 'indent_generated',
         'comment_removed', 'post_processed'),
        range(1, 7)))
    def __init__(self, stage="raw", module=None, object=None, debug=0, optimize=0,
                 lextab='lextab', reflags=0, nowarn=0, outputdir='',
                 debuglog=None, errorlog=None):
        self.lexer = lex(module, object, debug, optimize, lextab,
                         reflags, nowarn, outputdir, debuglog,
                         errorlog)
        if not stage in self._stages:
            raise ValueError("Unrecognized stage %r" % (stage,))
        self.stage = stage
        self._stage_level = self._stages[stage]

    def input(self, *a, **kw):
        self.lexer.input(*a, **kw)
        token_stream = iter(self.lexer.token, None)
        if self._stage_level >= 2:
            token_stream = detect_escaped(token_stream)
        if self._stage_level >= 3:
            token_stream = merge_escaped(token_stream)
        if self._stage_level >= 4:
            token_stream = indent_generator(token_stream)
        if self._stage_level >= 5:
            token_stream = remove_comments(token_stream)
        if self._stage_level >= 6:
            token_stream = post_process(token_stream, self.lexer.lexdata)
        self.token_stream = token_stream

    def token(self, *a, **kw):
        try:
            return gen_next(self.token_stream)
        except StopIteration:
            return None

    def __iter__(self):
        return iter(self.token, None)

def detect_escaped(stream):
    """Post process the given stream to generate escaped character for
    characters preceded by the escaping token."""
    for t in stream:
        if ESCAPING_CHAR[t.type]:
            try:
                t = gen_next(stream)
            except StopIteration:
                raise SyntaxError("EOF while escaping token %r (line %d)" %
                                  (t.value, t.lineno-1))
            t.escaped = True
        else:
            t.escaped = False
        yield t

def merge_escaped(stream):
    stream = Peeker(stream, EOF)
    queue = []

    t = gen_next(stream)
    while t:
        if t.escaped:
            queue.append(t)
        else:
            if t.type == "WORD":
                if queue:
                    queue.append(t)
                    n = stream.peek()
                    if not n.escaped:
                        t.value = "".join([c.value for c in queue])
                        yield t
                        queue = []
                else:
                    n = stream.peek()
                    if n.escaped:
                        queue.append(t)
                    else:
                        yield t
            else:
                if queue:
                    queue[-1].value = "".join([c.value for c in queue])
                    queue[-1].type = "WORD"
                    yield queue[-1]
                    queue = []
                yield t
        try:
            t = gen_next(stream)
        except StopIteration:
            if queue:
                t.value = "".join([c.value for c in queue])
                t.type = "WORD"
                yield t
            return

def skip_until_eol(stream, t):
    try:
        prev = stream.previous()
    except ValueError:
        prev = None
    while t.type != "NEWLINE":
        t = gen_next(stream)
    # FIXME: ideally, we would like to remove EOL for comments which span the
    # full line, but we need access to the token before the comment delimiter
    # to do so, as we don't want to remove EOL for inline commeng (e.g. 'foo #
    # comment')
    if prev and t.type == "NEWLINE" and prev.type in ('NEWLINE', 'INDENT'):
        t = gen_next(stream)
    return t

def remove_comments(stream):
    stream = BackwardGenerator(stream)
    for t in stream:
        if t.type == "SHARP":
            t = skip_until_eol(stream, t)
        yield t

def indent_generator(toks):
    """Post process the given stream of tokens to generate INDENT/DEDENT
    tokens.
    
    Note
    ----
    Each generated token's value is the total amount of spaces from the
    beginning of the line.
    
    The way indentation tokens are generated is similar to how it works in
    python."""
    stack = [0]

    # Dummy token to track the token just before the current one
    former = LexToken()
    former.type = "NEWLINE"
    former.value = "dummy"
    former.lineno = 0
    former.lexpos = -1

    def generate_dedent(stck, tok):
        amount = stck.pop(0)
        return new_dedent(amount, tok)

    for token in toks:
        if former.type == "NEWLINE":
            if token.type == "WS":
                indent = len(token.value)
            else:
                indent = 0

            if indent == stack[0]:
                former = token
                if indent > 0:
                    token = gen_next(toks)
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
                    former = gen_next(toks)
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
    tok = LexToken()
    tok.type = "INDENT"
    tok.value = amount
    tok.lineno = token.lineno
    tok.lexpos = token.lexpos
    return tok

def new_dedent(amount, token):
    tok = LexToken()
    tok.type = "DEDENT"
    tok.value = amount
    tok.lineno = token.lineno
    tok.lexpos = token.lexpos
    return tok

def _new_token(type, token):
    tok = LexToken()
    tok.type = type
    tok.value = token.value
    tok.lineno = token.lineno
    tok.lexpos = token.lexpos
    return tok

_FIELD_TYPE_TO_STATE = {
    "WORD": "SCANNING_WORD_FIELD",
    "WORDS": "SCANNING_WORDS_FIELD",
    "LINE": "SCANNING_SINGLELINE_FIELD",
    "MULTILINE": "SCANNING_MULTILINE_FIELD",
    "COMMA_LIST": "SCANNING_COMMA_LIST_FIELD"
}

def singleline_tokenizer(token, state, stream):
    if token.type == "NEWLINE":
        state = "SCANNING_FIELD_ID"
        queue = []
    else:
        queue = [token]

    try:
        tok = gen_next(stream)
    except StopIteration:
        tok = None

    return queue, tok, state

def multiline_tokenizer(token, state, stream, internal):
    stack = internal.stack
    queue = []

    if internal.stack_level is None:
        internal.stack_level = [len(internal.stack)]
    stack_level = internal.stack_level

    if token.type == "INDENT":
        stack.append(token)
        queue.insert(0, token)
    elif token.type == "DEDENT":
        stack.pop(0)
        if len(stack) < 1:
            state = "SCANNING_FIELD_ID"
        queue.insert(0, token)
    elif token.type == "NEWLINE":
        saved_newline = token
        # Case where there is a single, non indented line for the field, i.e.:
        # Description: a description
        if (len(stack) == stack_level[0] and stream.peek().type != "INDENT"):
            state = "SCANNING_FIELD_ID"
            internal.stack_level = None
        elif stream.peek().type == "DEDENT":
            try:
                while stream.peek().type == "DEDENT":
                    token = gen_next(stream)
                    queue.insert(0, token)
                    stack.pop()
            except StopIteration:
                pass
            if len(stack) == stack_level[0]:
                state = "SCANNING_FIELD_ID"
                internal.stack_level = None
            else:
                queue.append(saved_newline)
        else:
            queue.insert(0, token)
    else:
        queue.insert(0, token)

    try:
        token = gen_next(stream)
    except StopIteration:
        token = None
    return queue, token, state

def word_tokenizer(token, state, stream):
    queue = []
    state = "SCANNING_FIELD_ID"

    try:
        while token.type != "NEWLINE":
            if token.type == "WORD":
                queue.append(token)
            token = gen_next(stream)
    except StopIteration:
        token = None

    return queue, token, state

def words_tokenizer(token, state, stream, internal):
    token, state = _skip_ws(token, stream, state, internal)

    if state == "SCANNING_WORDS_FIELD":
        words_stack = internal.words_stack
        if token.type == "INDENT":
            words_stack.append(token)
        elif token.type == "DEDENT":
            words_stack.pop(0)
            if len(words_stack) < 1:
                state = "SCANNING_FIELD_ID"
                internal.words_stack = []
        queue = [token]
    else:
        queue = []
    try:
        tok = gen_next(stream)
    except StopIteration:
        tok = None
    return queue, tok, state

def scan_field_id(token, state, stream, lexdata):
    # When a candidate is found, do as follows:
    # - save the candidate
    # - eat any whitespace
    # - if next is colon, candidate is an identifier, emit both
    # identifier and colon
    candidate = token
    token = stream.peek()
    if token.type == "WS":
        token = stream.peek()
    if token.type == "COLON":
        # We do have a identifier, so replace WORD token by the
        # right keyword token
        candidate = _new_token(META_FIELDS_ID[candidate.value], candidate)

    try:
        field_type = FIELD_TYPE[candidate.type]
    except KeyError:
        data = lexdata.splitlines()
        msg = ["Error while tokenizing %r (missing colon ?)" %  candidate.value]
        msg += ["    Line %d -> %r" % (candidate.lineno, data[candidate.lineno-1])]
        raise SyntaxError("\n".join(msg))
    try:
        state = _FIELD_TYPE_TO_STATE[field_type]
    except KeyError:
        raise ValueError("Unknown state transition for type %s" % field_type)

    queue = [candidate]
    queue.append(gen_next(stream))
    nxt = gen_next(stream)
    return queue, nxt, state

def tokenize_conditional(stream, token):
    ret = []

    token.type = CONDITIONAL_ID[token.value]
    ret.append(token)

    queue = []
    nxt = stream.peek()
    if not nxt.type in ["COLON", "NEWLINE"]:
        while nxt.type not in ["COLON", "NEWLINE"]:
            if nxt.type not in ["WS"]:
                queue.append(nxt)
            nxt = gen_next(stream)
        queue.append(nxt)

    for q in queue:
        if q.value in CONDITIONAL_ID.keys():
            q.type = CONDITIONAL_ID[q.value]
        ret.append(q)

    return ret, gen_next(stream)

def comma_list_tokenizer(token, state, stream, internal):
    queue = []
    state = "SCANNING_FIELD_ID"

    def _filter_ws_before_comma(lst):
        ret = []
        for i, item in enumerate(lst):
            if item.type == "WS":
                if i < len(lst) and lst[i+1].type == "COMMA":
                    pass
                elif i > 0 and lst[i-1].type == "COMMA":
                    pass
                else:
                    ret.append(item)
            else:
                ret.append(item)
        return ret

    try:
        if token.type != "NEWLINE":
            token, state = _skip_ws(token, stream, state, internal)
        while token.type not in ("NEWLINE",):
            queue.append(token)
            token = gen_next(stream)
        # Eat newline
        token = gen_next(stream)
        if token.type == "INDENT":
            internal.stack.append(token)
            while token.type != "DEDENT":
                if token.type != "NEWLINE":
                    queue.append(token)
                token = gen_next(stream)
            if token.type == "DEDENT":
                internal.stack.pop(0)
            queue.append(token)
        return _filter_ws_before_comma(queue), gen_next(stream), state
    except StopIteration:
        return _filter_ws_before_comma(queue), None, "EOF"

    #return multiline_tokenizer(token, state, stream, internal)

def find_next(token, stream, internal):
    queue = []

    if token.type != "NEWLINE":
        if token.type == "INDENT":
            internal.stack.append(token)
        elif token.type == "DEDENT":
            internal.stack.pop(0)
        queue.append(token)

    try:
        tok = gen_next(stream)
    except StopIteration:
        tok = None

    return queue, tok

def post_process(stream, lexdata):
    # XXX: this is awfully complicated...
    class _Internal(object):
        def __init__(self):
            self.stack = []
            self.words_stack = []
            self.stack_level = None
    internal = _Internal()

    state = "SCANNING_FIELD_ID"

    stream = Peeker(stream)
    i = gen_next(stream)
    while i:
        if state == "SCANNING_FIELD_ID":
            if i.value in CONDITIONAL_ID.keys():
                queue, i = tokenize_conditional(stream, i)
                for q in queue:
                    yield q
            elif i.value in META_FIELDS_ID.keys():
                queue, i, state = scan_field_id(i, state, stream, lexdata)
                for q in queue:
                    yield q
            else:
                queue, i = find_next(i, stream, internal)
                for q in queue:
                    yield q
        elif state == "SCANNING_SINGLELINE_FIELD":
            queue, i, state = singleline_tokenizer(i, state, stream)
            for q in queue:
                yield q
        elif state == "SCANNING_MULTILINE_FIELD":
            queue, i, state = multiline_tokenizer(i, state, stream, internal)
            while len(queue) > 0:
                yield queue.pop()
        elif state == "SCANNING_WORD_FIELD":
            queue, i, state = word_tokenizer(i, state, stream)
            for t in queue:
                yield t
        elif state == "SCANNING_WORDS_FIELD":
            queue, i, state = words_tokenizer(i, state, stream, internal)
            for q in queue:
                yield q
        elif state == "SCANNING_COMMA_LIST_FIELD":
            queue, i, state = comma_list_tokenizer(i, state, stream, internal)
            for q in queue:
                yield q
        else:
            raise ValueError("Unknown state: %s" % state)

def _skip_ws(tok, stream, state, internal):
    while tok.type  in ["NEWLINE", "WS"]:
        if tok.type == "NEWLINE" and len(internal.words_stack) == 0:
            nxt = stream.peek()
            if not nxt.type == "INDENT":
                state = "SCANNING_FIELD_ID"
            else:
                tok = gen_next(stream)
            return tok, state
        tok = gen_next(stream)
    return tok, state
