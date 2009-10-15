import os

from toydist.compat.pyparsing import \
        Literal, WordStart, CharsNotIn, LineEnd, alphas, Word, \
        indentedBlock, OneOrMore, ZeroOrMore, OnlyOnce, \
        Group, empty, lineEnd, FollowedBy, col, alphanums, \
        Forward, Optional, delimitedList, \
        ParseException, ParseFatalException

#---------------------------------
#       Grammar definition
#---------------------------------
# Literals
colon = Literal(':').suppress()
comma_sep = Literal(',').suppress()
string = WordStart() + CharsNotIn('\n')
word = Word(alphas)
newline = LineEnd().suppress()
module_name = Word(alphanums + '_')
full_module_name = module_name + ZeroOrMore(Literal('.').suppress() + module_name)
filename = Word(alphanums + '.' + os.pathsep)

indent_stack = [1]

def checkPeerIndent(s,l,t):
    cur_col = col(l,s)
    if cur_col != indent_stack[-1]:
        if (not indent_stack) or cur_col > indent_stack[-1]:
            raise ParseFatalException(s, l, "illegal nesting")
        raise ParseException(s, l, "not a peer entry")

def checkSubIndent(s,l,t):
    cur_col = col(l,s)
    if cur_col > indent_stack[-1]:
        indent_stack.append(cur_col)
    else:
        raise ParseException(s, l, "not a subentry")

def checkUnindent(s,l,t):
    if l >= len(s):
        return
    cur_col = col(l,s)
    if not(cur_col < indent_stack[-1] and cur_col <= indent_stack[-2]):
        raise ParseException(s, l, "not an unindent")

def doUnindent():
    indent_stack.pop()

INDENT = lineEnd.suppress() + empty + empty.copy().setParseAction(checkSubIndent)
UNDENT = FollowedBy(empty).setParseAction(checkUnindent)
UNDENT.setParseAction(doUnindent)

stmt = Forward()
stmt.setParseAction(checkPeerIndent)

grammar = Group(OneOrMore(empty + stmt))

# metadata fields
name = Literal('Name')
name_definition = name + colon + word

summary = Literal('Summary')
summary_definition = summary + colon + string

author = Literal('Author')
author_definition = author + colon + string

indented_string = string.copy()
indented_string.setParseAction(checkPeerIndent)
multiline_string = Group(OneOrMore(empty + indented_string))

description_definition = Group(
        Literal("Description") + colon +
        INDENT + multiline_string + UNDENT)

metadata_field = (description_definition | name_definition | summary_definition \
        | author_definition)

# Modules section
modules = Literal("Modules")
modules_definition = modules + colon + \
        Group(full_module_name) + ZeroOrMore(comma_sep + Group(full_module_name))

# Extension section
extension_stmt = Forward()
extension_stmt.setParseAction(checkPeerIndent)

# sources subsection
src = Literal('sources')
src_files_line = filename + ZeroOrMore(comma_sep + filename)
src_definition = src + colon + \
        INDENT + \
        Group(OneOrMore(empty + indented_string)) + \
        UNDENT

extension_stmt << src_definition
        
extension_stmts = Group(OneOrMore(empty + extension_stmt))

extension = Literal("Extension")
extension_definition = \
        extension + colon + \
        Group(full_module_name) + \
        INDENT + extension_stmts + UNDENT

stmt << (metadata_field | modules_definition | extension_definition | src_definition)
