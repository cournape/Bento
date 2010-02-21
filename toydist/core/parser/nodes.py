class Node(object):
    def __init__(self, type, children=None, value=None):
        self.type = type
        if children:
            self.children = children
        else:
            self.children = []
        self.value = value

    def __str__(self):
        return "Node(%r)" % self.type

    def __repr__(self):
        return "Node(%r)" % self.type

def ast_pprint(root, cur_ind=0, ind_val=4, string=None):
    _buf = []

    def _ast_pprint(_root, _cur_ind):
        if not hasattr(_root, "children"):
            _buf.append(str(_root))
        if _root.children:
            _buf.append("%sNode(type='%s'):" % (' ' * _cur_ind * ind_val, _root.type))
            for c in _root.children:
                _ast_pprint(c, _cur_ind + 1)
        else:
            msg = "%sNode(type='%s'" % (' ' * _cur_ind * ind_val, _root.type)
            if _root.value is not None:
                msg += ", value=%r)" % _root.value
            else:
                msg += ")"
            _buf.append(msg)

    _ast_pprint(root, cur_ind)
    if string is None:
        print "\n".join(_buf)
    else:
        string.write("\n".join(_buf))
    
