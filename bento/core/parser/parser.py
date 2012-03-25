import sys
import errno

import os.path as op

from ply \
    import yacc

from bento.core.parser.lexer \
    import \
        MyLexer, tokens as _tokens

from bento._config \
    import \
        _PICKLED_PARSETAB, _OPTIMIZE_LEX, _DEBUG_YACC
from bento.core.parser.nodes \
    import \
        Node
from bento.core.errors \
    import \
        InternalBentoError, BentoError
from bento.core.utils \
    import \
        extract_exception
from bento.core.parser.errors \
    import \
        ParseError

# Do not remove: this is used by PLY
tokens = _tokens

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
            self.lexer = MyLexer(stage="post_processed", optimize=_OPTIMIZE_LEX)
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
        self.parser = yacc.yacc(start="stmt_list",
                                picklefile=picklefile,
                                debug=_DEBUG_YACC)

    def parse(self, data):
        res = self.parser.parse(data, lexer=self.lexer)
        # FIXME: this is stupid, deal correctly with empty ast in the grammar proper
        if res is None:
            res = Node("empty")
        return res

    def reset(self):
        # XXX: implements reset for lexer
        self.lexer = MyLexer(stage="post_processed", optimize=_OPTIMIZE_LEX)
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
            | library
            | exec
            | path
            | flag
            | extra_source_files
            | data_files
            | dummy
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
                 | meta_description_stmt
                 | meta_description_from_file_stmt
                 | meta_version_stmt
                 | meta_url_stmt
                 | meta_download_url_stmt
                 | meta_author_stmt
                 | meta_author_email_stmt
                 | meta_maintainer_stmt
                 | meta_maintainer_email_stmt
                 | meta_license_stmt
                 | meta_platforms_stmt
                 | meta_keywords_stmt
                 | meta_classifiers_stmt
                 | meta_hook_file_stmt
                 | meta_config_py_stmt
                 | meta_meta_template_file_stmt
                 | meta_subento_stmt
    """
    p[0] = p[1]

def p_meta_name_stmt(p):
    """meta_name_stmt : NAME_ID COLON WORD
    """
    p[0] = Node("name", value=p[3])

def p_meta_summary_stmt(p):
    """meta_summary_stmt : SUMMARY_ID COLON single_line_value
    """
    p[0] = Node("summary", value=p[3])

def p_meta_url_stmt(p):
    """meta_url_stmt : URL_ID COLON anyword
    """
    p[0] = Node("url", value=p[3].value)

def p_meta_download_url_stmt(p):
    """meta_download_url_stmt : DOWNLOAD_URL_ID COLON anyword
    """
    p[0] = Node("download_url", value=p[3].value)

def p_meta_author_stmt(p):
    """meta_author_stmt : AUTHOR_ID COLON single_line_value
    """
    p[0] = Node("author", value=p[3])

def p_meta_author_email_stmt(p):
    """meta_author_email_stmt : AUTHOR_EMAIL_ID COLON anyword
    """
    p[0] = Node("author_email", value=p[3].value)

def p_meta_maintainer_stmt(p):
    """meta_maintainer_stmt : MAINTAINER_ID COLON single_line_value
    """
    p[0] = Node("maintainer", value=p[3])

def p_meta_maintainer_email_stmt(p):
    """meta_maintainer_email_stmt : MAINTAINER_EMAIL_ID COLON anyword
    """
    p[0] = Node("maintainer_email", value=p[3].value)

def p_meta_license_stmt(p):
    """meta_license_stmt : LICENSE_ID COLON anyword
    """
    p[0] = Node("license", value=p[3].value)

def p_meta_description_from_file_stmt(p):
    """meta_description_from_file_stmt : DESCRIPTION_FROM_FILE_ID COLON anyword"""
    p[0] = Node("description_from_file", value=p[3].value)

def p_meta_platforms_stmt(p):
    """meta_platforms_stmt : PLATFORMS_ID COLON comma_list
    """
    p[0] = Node("platforms", value=p[3].value)

def p_meta_keywords_stmt(p):
    """meta_keywords_stmt : KEYWORDS_ID COLON comma_list
    """
    p[0] = Node("keywords", value=p[3].value)

def p_meta_version_stmt(p):
    """meta_version_stmt : VERSION_ID COLON version
    """
    p[0] = Node("version", value=p[3].value)

def p_meta_config_py_stmt(p):
    """meta_config_py_stmt : CONFIG_PY_ID COLON word
    """
    p[0] = Node("config_py", value=p[3].value)

def p_meta_meta_template_file_stmt(p):
    """meta_meta_template_file_stmt : META_TEMPLATE_FILE_ID COLON word
    """
    p[0] = Node("meta_template_file", value=p[3].value)

def p_meta_classifiers_stmt(p):
    """meta_classifiers_stmt : CLASSIFIERS_ID COLON classifiers_list"""
    p[0] = Node("classifiers", value=p[3].value)

def p_classifiers_list(p):
    """classifiers_list : indented_classifiers_list
    """
    p[0] = Node("classifiers", value=p[1].value)

def p_classifiers_list_term(p):
    """classifiers_list : classifiers
    """
    p[0] = Node("classifiers", value=p[1].value)

def p_indented_comma_list1(p):
    """indented_classifiers_list : classifiers COMMA INDENT classifiers DEDENT
    """
    p[0] = p[1]
    p[0].value.extend(p[4].value)

def p_indented_comma_list2(p):
    """indented_classifiers_list : INDENT classifiers DEDENT
    """
    p[0] = p[2]

def p_classifiers(p):
    """classifiers : classifiers COMMA classifier"""
    p[0] = p[1]
    p[0].value.append(p[3].value)

def p_classifiers_term(p):
    """classifiers : classifier"""
    p[0] = Node("classifiers", value=[p[1].value])

def p_classifier(p):
    """classifier : classifier classifier_atom"""
    p[0] = Node("classifier", value=(p[1].value + p[2].value))

def p_classifier_term(p):
    """classifier : classifier_atom"""
    p[0] = Node("classifier", value=p[1].value)

def p_classifier_atom(p):
    """classifier_atom : WORD
                       | WS
                       | DOUBLE_COLON
    """
    p[0] = Node("classifier", value=p[1])

def p_dummy(p):
    """dummy : AND BACKSLASH"""
    pass

def p_meta_subento_stmt(p):
    """meta_subento_stmt : SUBENTO_ID COLON comma_list"""
    p[0] = Node("subento", value=p[3].value)

def p_meta_hook_file_stmt(p):
    """meta_hook_file_stmt : HOOK_FILE_ID COLON comma_list
    """
    p[0] = Node("hook_files", value=p[3].value)

#---------------------------------------
# Data files and extra sources handling
#---------------------------------------
def p_extra_source_files(p):
    """extra_source_files : EXTRA_SOURCE_FILES_ID COLON comma_list"""
    p[0] = Node("extra_source_files", value=p[3].value)
 
def p_data_files(p):
    """data_files : data_files_declaration INDENT data_files_stmts DEDENT
    """
    p[0] = Node("data_files", children=[p[1]])
    p[0].children.append(p[3])

def p_data_files_declaration(p):
    """data_files_declaration : DATAFILES_ID COLON word"""
    p[0] = Node("data_files_declaration", value=p[3].value)

def p_data_files_stmts(p):
    """data_files_stmts : data_files_stmts data_files_stmt"""
    p[0] = Node("data_files_stmts", children=(p[1].children + [p[2]]))

def p_data_files_stmts_term(p):
    """data_files_stmts : data_files_stmt"""
    p[0] = Node("data_files_stmts", children=[p[1]])

def p_data_files_stmt(p):
    """data_files_stmt : data_files_target
                       | data_files_files
                       | data_files_srcdir
    """
    p[0] = p[1]

def p_data_files_target(p):
    """data_files_target : TARGET_ID COLON anyword"""
    p[0] = Node("target_dir", value=p[3].value)

def p_data_files_srcdir(p):
    """data_files_srcdir : SRCDIR_ID COLON anyword"""
    p[0] = Node("source_dir", value=p[3].value)

def p_data_files_files(p):
    """data_files_files : FILES_ID COLON comma_list"""
    p[0] = Node("files", value=p[3].value)

#---------------------
#   Library section
#---------------------
def p_library(p):
    """library : library_declaration INDENT library_stmts DEDENT
    """
    p[0] = Node("library", children=[p[1]])
    p[0].children.append(p[3])

def p_library_decl_only(p):
    """library : library_declaration
    """
    p[0] = Node("library", children=[p[1]])

def p_library_declaration(p):
    """library_declaration : LIBRARY_ID COLON library_name"""
    p[0] = p[3]

def p_library_name(p):
    """library_name : word
                    |"""
    if len(p) == 1:
        name = "default"
    else:
        name = p[1]
    p[0] = Node("library_name", value=name)

def p_library_stmts(p):
    """library_stmts : library_stmts library_stmt
    """
    children = p[1].children
    children.append(p[2])
    p[0] = Node("library_stmts", children=children)

def p_library_stmts_term(p):
    """library_stmts : library_stmt
    """
    p[0] = Node("library_stmts", children=[p[1]])

def p_library_stmt(p):
    """library_stmt : modules_stmt
                    | packages_stmt
                    | extension_stmt
                    | compiled_library_stmt
                    | build_requires_stmt
                    | install_requires_stmt
                    | conditional_stmt
                    | sub_directory_stmt
    """
    p[0] = p[1]

def p_packages_stmt(p):
    """packages_stmt : PACKAGES_ID COLON comma_list"""
    p[0] = Node("packages", value=p[3].value)

def p_modules_stmt(p):
    """modules_stmt : MODULES_ID COLON comma_list"""
    p[0] = Node("modules", value=p[3].value)

def p_build_requires_stmt(p):
    """build_requires_stmt : BUILD_REQUIRES_ID COLON comma_list"""
    p[0] = Node("build_requires", value=p[3].value)

def p_install_requires_stmt(p):
    """install_requires_stmt : INSTALL_REQUIRES_ID COLON comma_list"""
    p[0] = Node("install_requires", value=p[3].value)

def p_extension_stmt_content(p):
    """extension_stmt : extension_decl INDENT extension_field_stmts DEDENT"""
    p[0] = Node("extension", children=[p[1]])
    p[0].children.append(p[3])

def p_extension_field_stmts(p):
    """extension_field_stmts : extension_field_stmts extension_field_stmt"""
    children = p[1].children
    children.append(p[2])
    p[0] = Node("extension_field_stmts", children=children)

def p_extension_field_stmts_term(p):
    """extension_field_stmts : extension_field_stmt"""
    p[0] = Node("extension_field_stmts", children=[p[1]])

def p_extension_decl(p):
    """extension_decl : EXTENSION_ID COLON anyword"""
    p[0] = Node("extension_declaration", value=p[3].value)

def p_extension_sources(p):
    """extension_field_stmt : SOURCES_ID COLON comma_list"""
    p[0] = Node("sources", value=p[3].value)

def p_extension_include_dirs(p):
    """extension_field_stmt : INCLUDE_DIRS_ID COLON comma_list"""
    p[0] = Node("include_dirs", value=p[3].value)

def p_compiled_library_stmt_content(p):
    """compiled_library_stmt : compiled_library_decl INDENT compiled_library_field_stmts DEDENT"""
    p[0] = Node("compiled_library", children=[p[1]])
    p[0].children.append(p[3])

def p_compiled_library_field_stmts(p):
    """compiled_library_field_stmts : compiled_library_field_stmts compiled_library_field_stmt"""
    children = p[1].children
    children.append(p[2])
    p[0] = Node("compiled_library_field_stmts", children=children)

def p_compiled_library_field_stmts_term(p):
    """compiled_library_field_stmts : compiled_library_field_stmt"""
    p[0] = Node("compiled_library_field_stmts", children=[p[1]])

def p_compiled_library_decl(p):
    """compiled_library_decl : COMPILED_LIBRARY_ID COLON anyword"""
    p[0] = Node("compiled_library_declaration", value=p[3].value)

def p_compiled_library_sources(p):
    """compiled_library_field_stmt : SOURCES_ID COLON comma_list"""
    p[0] = Node("sources", value=p[3].value)

def p_compiled_library_include_dirs(p):
    """compiled_library_field_stmt : INCLUDE_DIRS_ID COLON comma_list"""
    p[0] = Node("include_dirs", value=p[3].value)

def p_sub_directory_stmt(p):
    """sub_directory_stmt : SUB_DIRECTORY_ID COLON word"""
    p[0] = Node("sub_directory", value=p[3].value)

#---------------------
# Conditional handling
#---------------------
def p_in_conditional_stmts(p):
    """in_conditional_stmts : library_stmts
                            | path_stmts
    """
    p[0] = p[1]

def p_conditional_if_error(p):
    """conditional_stmt : IF error"""
    raise ParseError(error_msg(p[2], "Error in if statement"))

def p_conditional_if_only(p):
    """conditional_stmt : IF test COLON INDENT in_conditional_stmts DEDENT"""
    p[0] = Node("conditional", value=p[2], children=[p[5]])

def p_conditional_if_else(p):
    """conditional_stmt : IF test COLON INDENT in_conditional_stmts DEDENT \
                          ELSE COLON INDENT in_conditional_stmts DEDENT
    """
    p[0] = Node("conditional", value=p[2], children=[p[5], p[10]])

def p_test(p):
    """test : bool
            | os_var
            | flag_var"""
    p[0] = p[1]

def p_os_var(p):
    """os_var : OS_OP LPAR word RPAR"""
    p[0] = Node("osvar", value=p[3])

def p_flag_var(p):
    """flag_var : FLAG_OP LPAR word RPAR"""
    p[0] = Node("flagvar", value=p[3])

def p_not_flag_var(p):
    """flag_var : NOT_OP FLAG_OP LPAR word RPAR"""
    p[0] = Node("not_flagvar", value=p[4])

def p_cond_expr_true(p):
    """bool : TRUE"""
    p[0] = Node("bool", value=True)

def p_cond_expr_true_not(p):
    """bool : NOT_OP FALSE"""
    p[0] = Node("bool", value=True)

def p_cond_expr_false(p):
    """bool : FALSE"""
    p[0] = Node("bool", value=False)

def p_cond_expr_false_not(p):
    """bool : NOT_OP TRUE"""
    p[0] = Node("bool", value=False)

#---------------------
#   Path section
#---------------------
def p_path(p):
    """path : path_declaration INDENT path_stmts DEDENT"""
    p[0] = Node("path", children=[p[1], p[3]])

def p_path_declaration(p):
    """path_declaration : PATH_ID COLON anyword"""
    p[0] = Node("path_declaration", value=p[3].value)

def p_path_stmts(p):
    """path_stmts : path_stmts path_stmt"""
    p[0] = Node("path_stmts", children=(p[1].children + [p[2]]))

def p_path_stmts_term(p):
    """path_stmts : path_stmt"""
    p[0] = Node("path_stmts", children=[p[1]])

def p_path_stmt(p):
    """path_stmt : path_description
                 | path_default
                 | conditional_stmt"""
    p[0] = p[1]

def p_path_description(p):
    """path_description : DESCRIPTION_ID COLON single_line_value"""
    #"""path_description : meta_description_stmt"""
    p[0] = Node("path_description", value=p[3])

def p_path_default(p):
    """path_default : DEFAULT_ID COLON anyword"""
    p[0] = Node("path_default", value=p[3].value)

#------------------
#   Flag section
#------------------
def p_flag(p):
    """flag : flag_declaration INDENT flag_stmts DEDENT"""
    p[0] = Node("flag", children=[p[1], p[3]])

def p_flag_declaration(p):
    """flag_declaration : FLAG_ID COLON anyword"""
    p[0] = Node("flag_declaration", value=p[3].value)

def p_flag_stmts(p):
    """flag_stmts : flag_stmts flag_stmt"""
    p[0] = Node("flag_stmts", children=(p[1].children + [p[2]]))

def p_flag_stmts_term(p):
    """flag_stmts : flag_stmt"""
    p[0] = Node("flag_stmts", children=[p[1]])

def p_flag_stmt(p):
    """flag_stmt : flag_description
                 | flag_default"""
    p[0] = p[1]

def p_flag_description(p):
    """flag_description : DESCRIPTION_ID COLON single_line_value"""
    #"""flag_description : meta_description_stmt"""
    p[0] = Node("flag_description", value=p[3])

def p_flag_default(p):
    """flag_default : DEFAULT_ID COLON anyword"""
    p[0] = Node("flag_default", value=p[3].value)

#----------------------
#  Executable section
#----------------------
def p_executable(p):
    """exec : exec_decl INDENT exec_stmts DEDENT"""
    p[0] = Node("executable", children=[p[1], p[3]])

def p_exec_declaration(p):
    """exec_decl : EXECUTABLE_ID COLON anyword"""
    p[0] = Node("exec_name", value=p[3].value)

def p_exec_stmts(p):
    """exec_stmts : exec_stmts exec_stmt"""
    p[0] = Node("exec_stmts", children=(p[1].children + [p[2]]))

def p_exec_stmts_term(p):
    """exec_stmts : exec_stmt"""
    p[0] = Node("exec_stmts", children=[p[1]])

def p_exec_stmt(p):
    """exec_stmt : function
                 | module"""
    p[0] = p[1]

def p_exec_module(p):
    """module : MODULE_ID COLON anyword"""
    p[0] = Node("module", value=p[3].value)

def p_exec_function(p):
    """function : FUNCTION_ID COLON anyword"""
    p[0] = Node("function", value=p[3].value)

#-----------------------
#   Literal handling
#-----------------------

def p_comma_list_indented(p):
    """comma_list : indented_comma_list 
    """
    p[0] = Node("comma_list", value=p[1].value)

def p_comma_list(p):
    """comma_list : comma_words
    """
    p[0] = Node("comma_list", value=p[1].value)

def p_indented_comma_list(p):
    """indented_comma_list : comma_words COMMA INDENT comma_words DEDENT
    """
    p[0] = p[1]
    p[0].value.extend(p[4].value)

def p_indented_comma_list_term(p):
    """indented_comma_list : INDENT comma_words DEDENT
    """
    p[0] = p[2]

def p_comma_words(p):
    """comma_words : comma_words COMMA anyword_comma_list
    """
    p[0] = p[1]
    p[0].value.append(p[3].value)

def p_comma_words_term(p):
    """comma_words : anyword_comma_list
    """
    p[0] = Node("comma_words", value=[p[1].value])

def p_single_line(p):
    """single_line_value : WS single_line"""
    p[0] = p[2]

def p_single_line_no_space(p):
    """single_line_value : single_line"""
    p[0] = p[1]

def p_single_line_string(p):
    """single_line : single_line literal"""
    p[0] = p[1] + [p[2]]

def p_single_line_string_term(p):
    """single_line : literal_no_space"""
    p[0] = [p[1]]

def p_meta_description_stmt_start_same_line(p):
    """meta_description_stmt : description_decl single_line_newline \
                               INDENT multi_stmts DEDENT
    """
    p[0] = Node("description", value=(p[2].value + p[4]))

def p_meta_description_stmt_indented_block(p):
    """meta_description_stmt : description_decl NEWLINE \
                               INDENT multi_stmts DEDENT
    """
    p[0] = Node("description", value=p[4])

def p_meta_description_stmt_indented_block2(p):
    """meta_description_stmt : description_decl WS NEWLINE \
                               INDENT multi_stmts DEDENT
    """
    p[0] = Node("description", value=p[5])

def p_meta_description_stmt_single(p):
    """meta_description_stmt : description_decl single_line_value
    """
    p[0] = Node("description", value=p[2])

def p_single_line_newline(p):
    """single_line_newline : single_line_value newline
    """
    p[0] = Node("single_line_newline", value=(p[1] + [p[2]]))

def p_description_decl(p):
    """description_decl : DESCRIPTION_ID COLON"""
    p[0] = Node("description_decl")

def p_indented_block(p):
    """indented_block : indent indented_block_value"""
    p[0] = [p[1]] + p[2]

def p_indented_block_value(p):
    """indented_block_value : multi_stmts dedent"""
    p[0] = p[1] + [p[2]]

def p_multi_stmts(p):
    """multi_stmts : multi_stmt multi_stmts"""
    p[0] = p[1] + p[2]

def p_multi_stmts_term(p):
    """multi_stmts : multi_stmt"""
    p[0] = p[1]

def p_multi_stmt_ind_block(p):
    """multi_stmt : indented_block"""
    p[0] = p[1]

def p_multi_stmt_term(p):
    """multi_stmt : multi_literal"""
    p[0] = [p[1]]

def p_newline(p):
    """newline : NEWLINE"""
    p[0] = Node("newline", value=p[1])

# anyword groks any character stream without space|newline
def p_anyword(p):
    """anyword : anyword literal"""
    p[0] = Node("anyword", value=(p[1].value + p[2].value))

def p_anyword_term(p):
    """anyword : literal"""
    p[0] = p[1]

def p_anyword_comma_list(p):
    """anyword_comma_list : anyword_comma_list anytoken_no_comma"""
    p[0] = Node("anyword_comma_list", value=(p[1].value + p[2].value))

def p_anyword_comma_list_term(p):
    """anyword_comma_list : anytoken_no_comma"""
    p[0] = Node("anyword_comma_list", value=p[1].value)

# Any token but whitespace, newline and comma
def p_anytoken_no_comma(p):
    """anytoken_no_comma : WORD
                         | COLON
                         | DOUBLE_COLON
                         | LPAR
                         | RPAR
                         | LESS
                         | SLASH
                         | SHARP
                         | EQUAL
                         | GREATER
    """
    p[0] = Node("anytoken", value=p[1])

def p_literal_no_space(p):
    """literal_no_space : anytoken_no_comma
    """
    p[0] = Node("literal", value=p[1].value)

def p_literal_no_space_term(p):
    """literal_no_space : COMMA
    """
    p[0] = Node("literal", value=p[1])

def p_literal(p):
    """literal : literal_no_space
    """
    p[0] = Node("literal", value=p[1].value)

def p_literal_term(p):
    """literal : WS
    """
    p[0] = Node("literal", value=p[1])

def p_multi_literal(p):
    """multi_literal : literal
    """
    p[0] = Node("multi_literal", value=p[1].value)

def p_multi_literal2(p):
    """multi_literal : newline
    """
    p[0] = p[1]

def p_indent(p):
    """indent : INDENT
    """
    p[0] = Node("indent", value=p[1])

def p_dedent(p):
    """dedent : DEDENT
    """
    p[0] = Node("dedent", value=p[1])

def p_word(p):
    """word : WORD"""
    p[0] = Node("word", value=p[1])

def p_version(p):
    """version : WORD"""
    p[0] = Node("version", value=p[1])

def p_error(p):
    # FIXME: this logic is buggy, think more about debug vs non-debug modes
    if _DEBUG_YACC:
        raise ParseError(error_msg(p, None))
    else:
        if p is None:
            raise InternalBentoError("Unknown parsing error (parser/lexer bug ? Please report this with your bento.info)")
        else:
            msg = "yacc: Syntax error at line %d, Token(%s, %r)" % \
                    (p.lineno, p.type, p.value)
            raise ParseError(msg, p)

def error_msg(p, error_msg):
    if p is not None:
        msg = ["Syntax error at line number %d, token %s (%r)" % \
               (p.lineno, p.type, p.value)]
        if error_msg is not None:
            msg += ["    %s" % error_msg]
        if hasattr(p.lexer, "lexdata"):
            data = p.lexer.lexdata.splitlines()
            msg += ["    Line %d -> %r" % (p.lineno, data[p.lineno-1])]
        else:
            msg += ["    Line %d" % (p.lineno)]
        return "\n".join(msg)
    return "Unhandled token"
