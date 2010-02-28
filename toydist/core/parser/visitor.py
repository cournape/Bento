import sys

from toydist.core.parser.nodes \
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

class Dispatcher(object):
    def __init__(self):
        self._d = {"libraries": {}, "paths": {}}
        self.action_dict = {
            "stmt_list": self.stmt_list,
            "name": self.name,
            "description": self.description,
            # Library
            "library": self.library,
            "library_name": self.library_name,
            "library_stmts": self.library_stmts,
            "modules": self.modules,
            "packages": self.packages,
            # Path
            "path": self.path,
            "path_default": self.path_default,
            "path_stmts": self.path_stmts,
            "path_description": self.path_description,
            "path_declaration": self.path_declaration,
            # Extension
            "extension": self.extension,
            "extension_declaration": self.extension_declaration,
            "sources": self.sources,
            # Conditional
            "conditional": self.conditional,
            "osvar": self.osvar,
        }

    def stmt_list(self, node):
        for c in node.children:
            if c.type in ["name", "description"]:
                self._d[c.type] = c.value
            elif c.type == "path":
                self._d["paths"][c.value["name"]] = c.value
            elif c.type == "library":
                self._d["libraries"][c.value["name"]] = c.value
        return self._d

    def name(self, node):
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
            if line[0].type == "dedent":
                while line[0].type == "dedent":
                    inds.pop(0)
                    line = line[1:]
                remain = line
            elif line[0].type == "indent":
                inds.insert(0, line[0].value - ind_shift)
                remain = line[1:]
            else:
                remain = line
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
        library = {
            "modules": [],
            "packages": [],
            "extensions": {}
        }

        def update(library_dict, c):
            if type(c) == list:
                for i in c:
                    update(library_dict, i)
            elif c.type == "name":
                library_dict["name"] = c.value
            elif c.type == "modules":
                library_dict["modules"].extend(c.value)
            elif c.type == "packages":
                library_dict["packages"].extend(c.value)
            elif c.type == "extension":
                name = c.value["name"]
                library_dict["extensions"][name] = c.value
            else:
                raise ValueError("Unhandled node type: %s" % c)

        for c in [node.children[0]] + node.children[1]:
            update(library, c)
        return Node("library", value=library)

    def library_name(self, node):
        return Node("name", value=node.value)

    def library_stmts(self, node):
        return node.children

    def packages(self, node):
        return node

    def modules(self, node):
        return node

    def extension(self, node):
        ret = {"sources": []}
        for c in node.children:
            if c.type == "name":
                ret["name"] = c.value
            elif c.type == "sources":
                ret["sources"].extend(c.value)
            else:
                raise ValueError("Gne ?")
        return Node("extension", value=ret)

    def extension_declaration(self, node):
        return Node("name", value=node.value)

    def sources(self, node):
        return node

    #-----------------
    #   Path option
    #-----------------
    def path(self, node):
        path = {}
        for i in [node.children[0]] + node.children[1]:
            if i.type == "path_declaration":
                path["name"] = i.value
            elif i.type == "path_description":
                path["description"] = i.value
            elif i.type == "default":
                path["default"] = i.value
            else:
                raise SyntaxError("GNe ?")

        return Node("path", value=path)

    def path_default(self, node):
        return Node("default", value=node.value)

    def path_stmts(self, node):
        return node.children

    def path_description(self, node):
        node.value = "".join([i.value for i in node.value])
        return node

    def path_declaration(self, node):
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
