import sys
import copy

from bento.core.parser.nodes \
    import \
        Node

def split_newline(s):
    try:
        ind = [i.type for i in s].index("newline")
        return [s[:ind+1], s[ind+1:]]
    except ValueError:
        return [s]

def split_newlines(s):
    t = []
    def _split_newlines(s):
        sp = split_newline(s)
        t.append(sp[0])
        if len(sp) > 1 and sp[1]:
            _split_newlines(sp[1])

    _split_newlines(s)
    return t

# XXX: fix the str vs bool issue with flag variables
_LIT_BOOL = {"true": True, "false": False, True: True, False: False}

class Dispatcher(object):
    def __init__(self, user_values=None):
        self._d = {
                "path_options": {},
                "flag_options": {},
                "libraries": {},
                "executables": {},
                "data_files": {},
                "extra_source_files": [],
        }
        self.action_dict = {
            "empty": self.empty,
            "stmt_list": self.stmt_list,
            "description": self.description,
            "description_from_file": self.description_from_file,
            "summary": self.summary,
            "author": self.author,
            "maintainer": self.author,
            "hook_files": self.hook_files,
            "config_py": self.config_py,
            "meta_template_file": self.meta_template_file,
            "subento": self.subento,
            # Library
            "library": self.library,
            "library_name": self.library_name,
            "library_stmts": self.library_stmts,
            # Path
            "path": self.path,
            "path_default": self.path_default,
            "path_stmts": self.path_stmts,
            "path_description": self.path_description,
            # Flag
            "flag": self.flag,
            "flag_default": self.flag_default,
            "flag_stmts": self.flag_stmts,
            "flag_description": self.flag_description,
            # Extension
            "extension": self.extension,
            "extension_declaration": self.extension_declaration,
            "extension_field_stmts": self.extension_field_stmts,
            # Pure C library
            "compiled_library": self.compiled_library,
            "compiled_library_declaration": self.compiled_library_declaration,
            "compiled_library_field_stmts": self.compiled_library_field_stmts,
            # Conditional
            "conditional": self.conditional,
            "osvar": self.osvar,
            "flagvar": self.flagvar,
            "not_flagvar": self.not_flagvar,
            "bool": self.bool_var,
            # Extra source files
            "extra_source_files": self.extra_source_files,
            # Data files handling
            "data_files": self.data_files,
            "data_files_stmts": self.data_files_stmts,
            # Executable
            "executable": self.executable,
            "exec_stmts": self.exec_stmts,
            "exec_name": self.exec_name,
            "function": self.function,
            "module": self.module,
            "sub_directory": self.sub_directory,
        }
        if user_values is not None:
            self._vars = copy.deepcopy(user_values)
        else:
            self._vars = {}

    def empty(self, node):
        return {}

    def stmt_list(self, node):
        for c in node.children:
            if c.type in ["name", "description", "version", "summary", "url",
                          "download_url", "author", "author_email",
                          "maintainer", "maintainer_email", "license",
                          "platforms", "classifiers", "hook_files",
                          "config_py", "description_from_file",
                          "meta_template_file", "keywords"]:
                self._d[c.type] = c.value
            elif c.type == "path":
                self._d["path_options"].update({c.value["name"]: c.value})
            elif c.type == "flag":
                self._d["flag_options"].update({c.value["name"]: c.value})
            elif c.type == "library":
                self._d["libraries"].update({c.value["name"]: c.value})
            elif c.type == "executable":
                self._d["executables"].update({c.value["name"]: c.value})
            elif c.type == "data_files":
                self._d["data_files"].update({c.value["name"]: c.value})
            else:
                raise ValueError("Unhandled top statement (%s)" % c)
        return self._d

    def summary(self, node):
        ret = Node(node.type)
        ret.value = "".join([i.value for i in node.value])
        return ret

    def author(self, node):
        node.value = "".join([i.value for i in node.value])
        return node

    def maintainer(self, node):
        node.value = "".join([i.value for i in node.value])
        return node

    def hook_files(self, node):
        if "hook_files" in self._d:
            self._d["hook_files"].extend(node.value)
        else:
            self._d["hook_files"] = node.value

    def config_py(self, node):
        return node

    def meta_template_file(self, node):
        return node

    def description_from_file(self, node):
        return node

    def description(self, node):
        tokens = []
        for i in node.value:
            if i.type in ["literal", "multi_literal", "newline",
                          "indent", "dedent", "single_line"]:
                tokens.append(i)

        # FIXME: fix grammar to get ind_shift
        ind_shift = 4
        inds = [0]
        line_str = []
        for line in split_newlines(tokens):
            # FIXME: this is horrible
            if line[0].type == "dedent":
                if set([node.type for node in line]) == set(["dedent"]): # if the line only contains dedent
                    inds.pop(0)
                    remain = [Node("literal", value="\n")]
                else:
                    while line[0].type == "dedent":
                        inds.pop(0)
                        line = line[1:]
                    remain = line
            elif line[0].type == "indent":
                inds.insert(0, line[0].value - ind_shift)
                remain = line[1:]
            else:
                remain = line

            if len(remain) > 0:
                if remain[-1].type == "dedent":
                    remain = remain[:-1]

            cur_line = [" " * inds[0]]
            cur_line.extend([t.value for t in remain])
            line_str.append("".join(cur_line))

        return Node("description", value="".join(line_str))

    #--------------------------
    # Library section handlers
    #--------------------------
    def library(self, node):
        library = {"py_modules": [],
                   "install_requires": [],
                   "build_requires": [],
                   "packages": [],
                   "extensions": {},
                   "compiled_libraries": {},
                   "sub_directory": None,
                   }

        def update(library_dict, c):
            if type(c) == list:
                for i in c:
                    update(library_dict, i)
            elif c.type == "name":
                library_dict["name"] = c.value
            elif c.type == "modules":
                library_dict["py_modules"].extend(c.value)
            elif c.type == "packages":
                library_dict["packages"].extend(c.value)
            elif c.type in ("build_requires", "install_requires"):
                library_dict[c.type].extend(c.value)
            elif c.type == "extension":
                name = c.value["name"]
                library_dict["extensions"][name] = c.value
            elif c.type == "compiled_library":
                name = c.value["name"]
                library_dict["compiled_libraries"][name] = c.value
            elif c.type == "sub_directory":
                library_dict["sub_directory"] = c.value
            else:
                raise ValueError("Unhandled node type: %s" % c)

        if len(node.children) > 1:
            nodes = [node.children[0]] + node.children[1]
        else:
            nodes = [node.children[0]]
        for c in nodes:
            update(library, c)
        return Node("library", value=library)

    def library_name(self, node):
        return Node("name", value=node.value)

    def library_stmts(self, node):
        return node.children

    def extension(self, node):
        ret = {}
        def update(extension_dict, c):
            if type(c) == list:
                for i in c:
                    update(extension_dict, i)
            elif c.type == "name":
                ret["name"] = c.value
            elif c.type == "sources":
                if "sources" in ret:
                    ret["sources"].extend(c.value)
                else:
                    ret["sources"] = c.value
            elif c.type == "include_dirs":
                if "include_dirs" in ret:
                    ret["include_dirs"].extend(c.value)
                else:
                    ret["include_dirs"] = c.value
            else:
                raise ValueError("Gne ?")
        for c in [node.children[0]] + node.children[1]:
            update(ret, c)
        return Node("extension", value=ret)

    def extension_field_stmts(self, node):
        return node.children

    def extension_declaration(self, node):
        return Node("name", value=node.value)

    def compiled_library(self, node):
        ret = {"sources": [], "include_dirs": []}
        def update(compiled_library_dict, c):
            if type(c) == list:
                for i in c:
                    update(compiled_library_dict, i)
            elif c.type == "name":
                ret["name"] = c.value
            elif c.type == "sources":
                ret["sources"].extend(c.value)
            elif c.type == "include_dirs":
                ret["include_dirs"].extend(c.value)
            else:
                raise ValueError("Unknown node %s" % c)
        for c in [node.children[0]] + node.children[1]:
            update(ret, c)
        return Node("compiled_library", value=ret)

    def compiled_library_field_stmts(self, node):
        return node.children

    def compiled_library_declaration(self, node):
        return Node("name", value=node.value)

    def sub_directory(self, node):
        return Node("sub_directory", value=node.value)

    #-----------------
    #   Path option
    #-----------------
    def path_stmts(self, node):
        return node.children

    def path(self, node):
        path = {}
        def update(c):
            if type(c) == list:
                for i in c:
                    update(i)
            elif c.type == "path_declaration":
                path["name"] = c.value
            elif c.type == "path_description":
                path["description"] = c.value
            elif c.type == "default":
                path["default"] = c.value
            elif c.type == "conditional_stmt":
                path["default"] = c.value
            else:
                raise SyntaxError("GNe ?")
        if len(node.children) > 1:
            nodes = [node.children[0]] + node.children[1]
        else:
            nodes = [node.children[0]]
        for node in nodes:
            update(node)

        if not "description" in path or not "default" in path:
            raise ValueError("Missing description in path section %r" %
                             (path["name"],))
        return Node("path", value=path)

    def path_default(self, node):
        return Node("default", value=node.value)

    def path_stmts(self, node):
        return node.children

    def path_description(self, node):
        node.value = "".join([i.value for i in node.value])
        return node

    #-----------------
    #   Flag option
    #-----------------
    # XXX: refactor path/flag handling, as they are almost identical
    def flag(self, node):
        flag = {}
        for i in [node.children[0]] + node.children[1]:
            if i.type == "flag_declaration":
                flag["name"] = i.value
            elif i.type == "flag_description":
                flag["description"] = i.value
            elif i.type == "default":
                flag["default"] = i.value
            else:
                raise SyntaxError("GNe ?")

        if not flag["default"] in ["true", "false"]:
            raise SyntaxError("invalid default value %s for flag %s" \
                              % (flag["default"], flag["name"])) 

        if not flag["name"] in self._vars:
            self._vars[flag["name"]] = flag["default"]

        return Node("flag", value=flag)

    def flag_default(self, node):
        return Node("default", value=node.value)

    def flag_stmts(self, node):
        return node.children

    def flag_description(self, node):
        node.value = "".join([i.value for i in node.value])
        return node

    #-------------------
    #   Conditionals
    #-------------------
    def conditional(self, node):
        test = node.value
        if self.action_dict[test.type](test):
            return node.children[:1]
        else:
            return node.children[1:]

    def osvar(self, node):
        os_name = node.value.value
        return os_name == sys.platform

    def bool_var(self, node):
        return node.value

    def not_flagvar(self, node):
        name = node.value.value
        try:
            value = self._vars[name]
        except KeyError:
            raise ValueError("Unknown flag variable %s" % name)
        else:
            return not _LIT_BOOL[value]

    def flagvar(self, node):
        name = node.value.value
        try:
            value = self._vars[name]
        except KeyError:
            raise ValueError("Unknown flag variable %s" % name)
        else:
            return _LIT_BOOL[value]

    def extra_source_files(self, node):
        self._d["extra_source_files"].extend(node.value)

    def subento(self, node):
        if "subento" in self._d:
            self._d["subento"].extend(node.value)
        else:
            self._d["subento"] = node.value

    # Data handling
    def data_files(self, node):
        d = {}

        def update(data_d, c):
            if type(c) == list:
                for  i in c:
                    update(data_d, i)
            elif c.type == "data_files_declaration":
                d["name"] = c.value
            elif c.type == "source_dir":
                d["source_dir"] = c.value
            elif c.type == "target_dir":
                d["target_dir"] = c.value
            elif c.type == "files":
                d["files"] = c.value
            else:
                raise ValueError("Unhandled node type: %s" % c)

        for c in node.children:
            update(d, c)

        return Node("data_files", value=d)

    def data_files_stmts(self, node):
        return node.children

    # Executable handling
    def executable(self, node):
        d = {}

        def update(exec_d, c):
            if type(c) == list:
                for  i in c:
                    update(exec_d, i)
            elif c.type == "name":
                exec_d["name"] = c.value
            elif c.type == "module":
                exec_d["module"] = c.value
            elif c.type == "function":
                exec_d["function"] = c.value
            else:
                raise ValueError("Unhandled node type: %s" % c)

        for c in node.children:
            update(d, c)

        return Node("executable", value=d)

    def exec_stmts(self, node):
        return node.children

    def exec_name(self, node):
        return Node("name", value=node.value)

    def function(self, node):
        return Node("function", value=node.value)

    def module(self, node):
        return Node("module", value=node.value)
