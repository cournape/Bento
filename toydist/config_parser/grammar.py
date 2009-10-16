import os

from toydist.compat.pyparsing import \
        Literal, WordStart, CharsNotIn, LineEnd, alphas, Word, \
        indentedBlock, OneOrMore, ZeroOrMore, OnlyOnce, \
        Group, empty, lineEnd, FollowedBy, col, alphanums, \
        Forward, Optional, delimitedList, \
        ParseException, ParseFatalException, nums

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
version_string = string.copy()

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

grammar = OneOrMore(empty + stmt)

# metadata fields
name = Literal('Name')
name_definition = name + colon + word.setResultsName('name')

summary = Literal('Summary')
summary_definition = summary + colon + string.setResultsName('summary')

author = Literal('Author')
author_definition = author + colon + string.setResultsName('author')

author_email = Literal('AuthorEmail')
author_email_definition = author_email + colon + string.setResultsName('author_email')

maintainer = Literal('Maintainer')
maintainer_definition = maintainer + colon + string.setResultsName('maintainer')

maintainer_email = Literal('MaintainerEmail')
maintainer_email_definition = maintainer_email + colon + \
        string.setResultsName('maintainer_email')

indented_string = string.copy()
indented_string.setParseAction(checkPeerIndent)
multiline_string = Group(OneOrMore(empty + indented_string))

description_definition = \
        Literal("Description") + colon + \
        INDENT + multiline_string.setResultsName('description') + UNDENT

version = Literal('Version')
version_definition = version + colon + version_string.setResultsName('version')

metadata_field = (description_definition | name_definition | summary_definition \
        | author_definition | author_email_definition \
        | maintainer_email_definition | maintainer_definition \
        | version_definition)

# Modules section
modules = Literal("Modules")
modules_names = Group(full_module_name) + ZeroOrMore(comma_sep + Group(full_module_name))
modules_definition = modules + colon + modules_names.setResultsName('modules')


# Package section
package = Literal("Package")
package_names = Group(full_module_name) + ZeroOrMore(comma_sep + Group(full_module_name))
package_definition = package + colon + package_names.setResultsName('packages')
        

# Extension section
extension_stmt = Forward()
extension_stmt.setParseAction(checkPeerIndent)

# sources subsection
src = Literal('sources')
src_files_line = filename + ZeroOrMore(comma_sep + filename)
src_value = Group(OneOrMore(empty + indented_string))
src_definition = src + colon + \
        INDENT + \
        src_value.setResultsName('extension_src') + \
        UNDENT

extension_stmt << src_definition
        
extension_stmts = OneOrMore(empty + extension_stmt)

extension = Literal("Extension")
extension_name = Group(full_module_name)
extension_definition = \
        extension + colon + \
        extension_name.setResultsName('extension_name') + \
        INDENT + extension_stmts + UNDENT

stmt << (metadata_field | modules_definition | package_definition | \
         extension_definition | src_definition)
