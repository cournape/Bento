import warnings

from bento.parser.nodes import Node

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
    p[0] = Node("stmt_list", [])

def p_stmt(p):
    """stmt : meta_stmt
            | data_files
            | exec
            | extra_source_files
            | flag
            | library
            | path
    """
    p[0] = p[1]

def p_empty(p):
    "empty :"
    pass

#----------------
#   Meta data
#----------------
def p_meta_stmt(p):
    """meta_stmt : meta_author_stmt
                 | meta_author_email_stmt
                 | meta_classifiers_stmt
                 | meta_config_py_stmt
                 | meta_description_stmt
                 | meta_description_from_file_stmt
                 | meta_download_url_stmt
                 | meta_hook_file_stmt
                 | meta_keywords_stmt
                 | meta_license_stmt
                 | meta_maintainer_stmt
                 | meta_maintainer_email_stmt
                 | meta_name_stmt
                 | meta_platforms_stmt
                 | meta_recurse_stmt
                 | meta_summary_stmt
                 | meta_meta_template_files_stmt
                 | meta_use_backends_stmt
                 | meta_url_stmt
                 | meta_version_stmt
    """
    p[0] = p[1]

def p_meta_description(p):
    """meta_description_stmt : DESCRIPTION_ID COLON MULTILINES_STRING
    """
    p[0] = Node("description", value=p[3])

def p_meta_description_indented(p):
    """meta_description_stmt : DESCRIPTION_ID COLON INDENT MULTILINES_STRING DEDENT
    """
    p[0] = Node("description", value=p[4])

def p_meta_name_stmt(p):
    """meta_name_stmt : NAME_ID COLON WORD
    """
    p[0] = Node("name", value=p[3])

def p_meta_summary_stmt(p):
    """meta_summary_stmt : SUMMARY_ID COLON STRING
    """
    p[0] = Node("summary", value=p[3])

def p_meta_url_stmt(p):
    """meta_url_stmt : URL_ID COLON WORD
    """
    p[0] = Node("url", value=p[3])

def p_meta_download_url_stmt(p):
    """meta_download_url_stmt : DOWNLOAD_URL_ID COLON WORD
    """
    p[0] = Node("download_url", value=p[3])

def p_meta_author_stmt(p):
    """meta_author_stmt : AUTHOR_ID COLON STRING
    """
    p[0] = Node("author", value=p[3])

def p_meta_author_email_stmt(p):
    """meta_author_email_stmt : AUTHOR_EMAIL_ID COLON WORD
    """
    p[0] = Node("author_email", value=p[3])

def p_meta_maintainer_stmt(p):
    """meta_maintainer_stmt : MAINTAINER_ID COLON STRING
    """
    p[0] = Node("maintainer", value=p[3])

def p_meta_maintainer_email_stmt(p):
    """meta_maintainer_email_stmt : MAINTAINER_EMAIL_ID COLON WORD
    """
    p[0] = Node("maintainer_email", value=p[3])

def p_meta_license_stmt(p):
    """meta_license_stmt : LICENSE_ID COLON STRING
    """
    p[0] = Node("license", value=p[3])

def p_meta_description_from_file_stmt(p):
    """meta_description_from_file_stmt : DESCRIPTION_FROM_FILE_ID COLON WORD"""
    p[0] = Node("description_from_file", value=p[3])

def p_meta_platforms_stmt(p):
    """meta_platforms_stmt : PLATFORMS_ID COLON scomma_list
    """
    p[0] = Node("platforms", value=p[3].value)

def p_meta_keywords_stmt(p):
    """meta_keywords_stmt : KEYWORDS_ID COLON wcomma_list
    """
    p[0] = Node("keywords", value=p[3].value)

def p_meta_version_stmt(p):
    """meta_version_stmt : VERSION_ID COLON version
    """
    p[0] = Node("version", value=p[3].value)

def p_meta_config_py_stmt(p):
    """meta_config_py_stmt : CONFIG_PY_ID COLON WORD
    """
    p[0] = Node("config_py", value=p[3])

def p_meta_meta_template_file_stmt(p):
    """meta_meta_template_files_stmt : META_TEMPLATE_FILE_ID COLON WORD
    """
    warnings.warn("MetaTemplateFile field is obsolete - use MetaTemplateFiles itself")
    p[0] = Node("meta_template_files", value=[p[3]])

def p_meta_meta_template_files_stmt(p):
    """meta_meta_template_files_stmt : META_TEMPLATE_FILES_ID COLON wcomma_list
    """
    p[0] = Node("meta_template_files", value=p[3].value)

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
    """classifier : STRING"""
    p[0] = Node("classifier", value=p[1])

def p_meta_hook_file_stmt(p):
    """meta_hook_file_stmt : HOOK_FILE_ID COLON wcomma_list
    """
    p[0] = Node("hook_files", value=p[3].value)

def p_meta_subento_stmt(p):
    """meta_recurse_stmt : RECURSE_ID COLON wcomma_list"""
    p[0] = Node("subento", value=p[3].value)

def p_meta_use_backends_stmt(p):
    """meta_use_backends_stmt : USE_BACKENDS_ID COLON wcomma_list"""
    p[0] = Node("use_backends", value=p[3].value)

#---------------------------------------
# Data files and extra sources handling
#---------------------------------------
def p_extra_source_files(p):
    """extra_source_files : EXTRA_SOURCE_FILES_ID COLON wcomma_list"""
    p[0] = Node("extra_source_files", value=p[3].value)
 
def p_data_files(p):
    """data_files : data_files_declaration INDENT data_files_stmts DEDENT
    """
    p[0] = Node("data_files", children=[p[1]])
    p[0].children.append(p[3])

def p_data_files_declaration(p):
    """data_files_declaration : DATAFILES_ID COLON WORD"""
    p[0] = Node("data_files_declaration", value=p[3])

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
    """data_files_target : TARGET_ID COLON WORD"""
    p[0] = Node("target_dir", value=p[3])

def p_data_files_srcdir(p):
    """data_files_srcdir : SRCDIR_ID COLON WORD"""
    p[0] = Node("source_dir", value=p[3])

def p_data_files_files(p):
    """data_files_files : FILES_ID COLON wcomma_list"""
    p[0] = Node("files", value=p[3].value)

#------------------
#   Flag section
#------------------
def p_flag(p):
    """flag : flag_declaration INDENT flag_stmts DEDENT"""
    p[0] = Node("flag", children=[p[1], p[3]])

def p_flag_declaration(p):
    """flag_declaration : FLAG_ID COLON WORD"""
    p[0] = Node("flag_declaration", value=p[3])

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
    """flag_description : DESCRIPTION_ID COLON STRING"""
    p[0] = Node("flag_description", value=p[3])

def p_flag_default(p):
    """flag_default : DEFAULT_ID COLON WORD"""
    p[0] = Node("flag_default", value=p[3])

#---------------------
#   Path section
#---------------------
def p_path(p):
    """path : path_declaration INDENT path_stmts DEDENT"""
    p[0] = Node("path", children=[p[1], p[3]])

def p_path_declaration(p):
    """path_declaration : PATH_ID COLON WORD"""
    p[0] = Node("path_declaration", value=p[3])

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
    """path_description : DESCRIPTION_ID COLON STRING"""
    #"""path_description : meta_description_stmt"""
    p[0] = Node("path_description", value=p[3])

def p_path_default(p):
    """path_default : DEFAULT_ID COLON WORD"""
    p[0] = Node("path_default", value=p[3])

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
    """library_name : WORD
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
    """library_stmt : build_requires_stmt
                    | compiled_library_stmt
                    | conditional_stmt
                    | extension_stmt
                    | modules_stmt
                    | packages_stmt
                    | sub_directory_stmt
    """
    p[0] = p[1]

def p_packages_stmt(p):
    """packages_stmt : PACKAGES_ID COLON wcomma_list"""
    p[0] = Node("packages", value=p[3].value)

def p_modules_stmt(p):
    """modules_stmt : MODULES_ID COLON wcomma_list"""
    p[0] = Node("modules", value=p[3].value)

def p_sub_directory_stmt(p):
    """sub_directory_stmt : SUB_DIRECTORY_ID COLON WORD"""
    p[0] = Node("sub_directory", value=p[3])

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
    """extension_decl : EXTENSION_ID COLON WORD"""
    p[0] = Node("extension_declaration", value=p[3])

def p_extension_sources(p):
    """extension_field_stmt : SOURCES_ID COLON wcomma_list"""
    p[0] = Node("sources", value=p[3].value)

def p_extension_include_dirs(p):
    """extension_field_stmt : INCLUDE_DIRS_ID COLON wcomma_list"""
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
    """compiled_library_decl : COMPILED_LIBRARY_ID COLON WORD"""
    p[0] = Node("compiled_library_declaration", value=p[3])

def p_compiled_library_sources(p):
    """compiled_library_field_stmt : SOURCES_ID COLON wcomma_list"""
    p[0] = Node("sources", value=p[3].value)

def p_compiled_library_include_dirs(p):
    """compiled_library_field_stmt : INCLUDE_DIRS_ID COLON wcomma_list"""
    p[0] = Node("include_dirs", value=p[3].value)

def p_build_requires_stmt(p):
    """build_requires_stmt : BUILD_REQUIRES_ID COLON scomma_list"""
    p[0] = Node("build_requires", value=p[3].value)

def p_install_requires_stmt(p):
    """build_requires_stmt : INSTALL_REQUIRES_ID COLON scomma_list"""
    p[0] = Node("install_requires", value=p[3].value)

#---------------------
# Conditional handling
#---------------------
def p_in_conditional_stmts(p):
    """in_conditional_stmts : library_stmts
                            | path_stmts
    """
    p[0] = p[1]

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
    """os_var : OS_OP LPAR WORD RPAR"""
    p[0] = Node("osvar", value=p[3])

def p_flag_var(p):
    """flag_var : FLAG_OP LPAR WORD RPAR"""
    p[0] = Node("flagvar", value=p[3])

def p_not_flag_var(p):
    """flag_var : NOT_OP FLAG_OP LPAR WORD RPAR"""
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

#----------------------
#  Executable section
#----------------------
def p_executable(p):
    """exec : exec_decl INDENT exec_stmts DEDENT"""
    p[0] = Node("executable", children=[p[1], p[3]])

def p_exec_declaration(p):
    """exec_decl : EXECUTABLE_ID COLON WORD"""
    p[0] = Node("exec_name", value=p[3])

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
    """module : MODULE_ID COLON WORD"""
    p[0] = Node("module", value=p[3])

def p_exec_function(p):
    """function : FUNCTION_ID COLON WORD"""
    p[0] = Node("function", value=p[3])

# List of words handling
def p_wcomma_list_indented(p):
    """wcomma_list : comma_words COMMA INDENT comma_words DEDENT
    """
    p[0] = Node("wcomma_list", value=(p[1].value + p[4].value))

def p_wcomma_list_indented2(p):
    """wcomma_list : INDENT comma_words DEDENT
    """
    p[0] = Node("wcomma_list", value=p[2].value)

def p_wcomma_list(p):
    """wcomma_list : comma_words
    """
    p[0] = Node("wcomma_list", value=p[1].value)

#def p_indented_wcomma_list(p):
#    """indented_wcomma_list : WORD COMMA INDENT comma_words DEDENT
#    """
#    p[0] = p[1]
#    p[0].value.extend(p[4].value)
#
#def p_indented_wcomma_list_term(p):
#    """indented_comma_list : INDENT comma_words DEDENT
#    """
#    p[0] = p[2]

def p_comma_words(p):
    """comma_words : comma_words COMMA WORD
    """
    p[0] = p[1]
    p[0].value.append(p[3])

def p_comma_words_term(p):
    """comma_words : WORD
    """
    p[0] = Node("comma_words", value=[p[1]])

# List of strings handling
def p_scomma_list_indented(p):
    """scomma_list : indented_scomma_list 
    """
    p[0] = Node("scomma_list", value=p[1].value)

def p_scomma_list(p):
    """scomma_list : comma_strings
    """
    p[0] = Node("scomma_list", value=p[1].value)

def p_indented_scomma_list(p):
    """indented_scomma_list : comma_strings COMMA INDENT comma_strings DEDENT
    """
    p[0] = p[1]
    p[0].value.extend(p[4].value)

def p_indented_scomma_list_term(p):
    """indented_scomma_list : INDENT comma_strings DEDENT
    """
    p[0] = p[2]

def p_comma_strings(p):
    """comma_strings : comma_strings COMMA STRING
    """
    p[0] = p[1]
    p[0].value.append(p[3])

def p_comma_strings_term(p):
    """comma_strings : STRING
    """
    p[0] = Node("comma_strings", value=[p[1]])

# FIXME: proper literal for version
def p_version(p):
    """version : WORD"""
    p[0] = Node("version", value=p[1])
