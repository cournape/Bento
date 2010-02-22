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
        self._d = {}
        self.action_dict = {
            "stmt_list": self.stmt_list,
            "name": self.name,
            "description": self.description,
        }

    def stmt_list(self, node):
        for c in node.children:
            self._d.update(c)
        return self._d

    def name(self, node):
        return {"name": node.value}

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
            print line
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
            print cur_line
            line_str.append("".join(cur_line))

        return {"description": "".join(line_str)}
