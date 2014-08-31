"""
Ripped off from waf (v 1.6), by Thomas Nagy

The cool design is his, bugs most certainly mine :)
"""

import os, shutil, re, sys

def split_path(path):
    return path.split('/')

def split_path_cygwin(path):
    if path.startswith('//'):
        ret = path.split('/')[2:]
        ret[0] = '/' + ret[0]
        return ret
    return path.split('/')

re_sp = re.compile('[/\\\\]')
def split_path_win32(path):
    if path.startswith('\\\\'):
        ret = re.split(re_sp, path)[2:]
        ret[0] = '\\' + ret[0]
        return ret
    return re.split(re_sp, path)

if sys.platform == 'cygwin':
    split_path = split_path_cygwin
elif sys.platform == 'win32':
    split_path = split_path_win32

class Node(object):
    """
    This class is divided into two parts, the basic methods meant for filesystem access, and
    the ones which are bound to a context (the build context). The imports do not reflect this.
    """

    __slots__ = ('name', 'sig', 'children', 'parent', 'cache_abspath', 'cache_isdir')
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent

        if parent:
            if name in parent.children:
                raise Errors.WafError('node %s exists in the parent files %r already' % (name, parent))
            parent.children[name] = self

    def __setstate__(self, data):
        self.name = data[0]
        self.parent = data[1]
        if data[2] is not None:
            self.children = data[2]
        if data[3] is not None:
            self.sig = data[3]

    def __getstate__(self):
        return (self.name, self.parent, getattr(self, 'children', None), getattr(self, 'sig', None))

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.abspath()

    def __hash__(self):
        return id(self) # TODO see if it is still the case
        #raise Errors.WafError('do not hash nodes (too expensive)')

    def __eq__(self, node):
        return id(self) == id(node)

    def __copy__(self):
        "nodes are not supposed to be copied"
        raise Errors.WafError('nodes are not supposed to be copied')

    def read(self, flags='r'):
        "get the contents, assuming the node is a file"
        fid = open(self.abspath(), flags)
        try:
            return fid.read()
        finally:
            fid.close()

    def write(self, data, flags='w'):
        "write some text to the physical file, assuming the node is a file"
        f = None
        try:
            f = open(self.abspath(), flags)
            f.write(data)
        finally:
            if f:
                f.close()

    def chmod(self, val):
        "change file/dir permissions"
        os.chmod(self.abspath(), val)

    def delete(self):
        "delete the file physically, do not destroy the nodes"
        try:
            shutil.rmtree(self.abspath())
        except:
            pass

        try:
            delattr(self, 'children')
        except:
            pass

    def suffix(self):
        "scons-like - hot zone so do not touch"
        k = max(0, self.name.rfind('.'))
        return self.name[k:]

    def height(self):
        "amount of parents"
        d = self
        val = -1
        while d:
            d = d.parent
            val += 1
        return val

    def listdir(self):
        "list the directory contents"
        return os.listdir(self.abspath())

    def mkdir(self):
        "write a directory for the node"
        if getattr(self, 'cache_isdir', None):
            return

        try:
            self.parent.mkdir()
        except:
            pass

        if self.name:
            try:
                os.mkdir(self.abspath())
            except OSError:
                pass

            if not os.path.isdir(self.abspath()):
                raise IOError('%s is not a directory' % self)

            try:
                self.children
            except:
                self.children = {}

        self.cache_isdir = True

    def find_node(self, lst):
        "read the file system, make the nodes as needed"

        if isinstance(lst, str):
            lst = [x for x in split_path(lst) if x and x != '.']

        cur = self
        for x in lst:
            if x == '..':
                cur = cur.parent
                continue

            try:
                if x in cur.children:
                    cur = cur.children[x]
                    continue
            except:
                cur.children = {}

            # optimistic: create the node first then look if it was correct to do so
            cur = self.__class__(x, cur)
            try:
                os.stat(cur.abspath())
            except:
                del cur.parent.children[x]
                return None

        ret = cur

        try:
            while not getattr(cur.parent, 'cache_isdir', None):
                cur = cur.parent
                cur.cache_isdir = True
        except AttributeError:
            pass

        return ret

    def make_node(self, lst):
        "make a branch of nodes"
        if isinstance(lst, str):
            lst = [x for x in split_path(lst) if x and x != '.']

        cur = self
        for x in lst:
            if x == '..':
                cur = cur.parent
                continue

            if getattr(cur, 'children', {}):
                if x in cur.children:
                    cur = cur.children[x]
                    continue
            else:
                cur.children = {}
            cur = self.__class__(x, cur)
        return cur

    def search(self, lst):
        "dumb search for existing nodes"
        if isinstance(lst, str):
            lst = [x for x in split_path(lst) if x and x != '.']

        cur = self
        try:
            for x in lst:
                if x == '..':
                    cur = cur.parent
                else:
                    cur = cur.children[x]
            return cur
        except:
            pass

    def path_from(self, node):
        """path of this node seen from the other
            self = foo/bar/xyz.txt
            node = foo/stuff/
            -> ../bar/xyz.txt
        """
        # common root in rev 7673

        c1 = self
        c2 = node

        c1h = c1.height()
        c2h = c2.height()

        lst = []
        up = 0

        while c1h > c2h:
            lst.append(c1.name)
            c1 = c1.parent
            c1h -= 1

        while c2h > c1h:
            up += 1
            c2 = c2.parent
            c2h -= 1

        while id(c1) != id(c2):
            lst.append(c1.name)
            up += 1

            c1 = c1.parent
            c2 = c2.parent

        for i in range(up):
            lst.append('..')
        lst.reverse()
        return os.sep.join(lst) or '.'

    def abspath(self):
        """
        absolute path
        cache into the build context, cache_node_abspath
        """
        try:
            return self.cache_abspath
        except:
            pass
        # think twice before touching this (performance + complexity + correctness)
        if not self.parent:
            val = os.sep == '/' and os.sep or ''
        elif not self.parent.name:
            # drive letter for win32
            val = (os.sep == '/' and os.sep or '') + self.name
        else:
            val = self.parent.abspath() + os.sep + self.name

        self.cache_abspath = val
        return val

    def is_child_of(self, node):
        "does this node belong to the subtree node"
        p = self
        diff = self.height() - node.height()
        while diff > 0:
            diff -= 1
            p = p.parent
        return id(p) == id(node)

    # --------------------------------------------------------------------------------
    # the following methods require the source/build folders (bld.srcnode/bld.bldnode)
    # using a subclass is a possibility, but is that really necessary?
    # --------------------------------------------------------------------------------

    def is_src(self):
        """note: !is_src does not imply is_bld()"""
        cur = self
        x = id(self.ctx.srcnode)
        y = id(self.ctx.bldnode)
        while cur.parent:
            if id(cur) == y:
                return False
            if id(cur) == x:
                return True
            cur = cur.parent
        return False

    def is_bld(self):
        """note: !is_bld does not imply is_src"""
        cur = self
        y = id(self.ctx.bldnode)
        while cur.parent:
            if id(cur) == y:
                return True
            cur = cur.parent
        return False

    def get_src(self):
        """for a build node, will return the equivalent src node (or self if not possible)"""
        cur = self
        x = id(self.ctx.srcnode)
        y = id(self.ctx.bldnode)
        lst = []
        while cur.parent:
            if id(cur) == y:
                lst.reverse()
                return self.ctx.srcnode.make_node(lst)
            if id(cur) == x:
                return self
            lst.append(cur.name)
            cur = cur.parent
        return self

    def get_bld(self):
        """for a src node, will return the equivalent bld node (or self if not possible)"""
        cur = self
        x = id(self.ctx.srcnode)
        y = id(self.ctx.bldnode)
        lst = []
        while cur.parent:
            if id(cur) == y:
                return self
            if id(cur) == x:
                lst.reverse()
                return self.ctx.bldnode.make_node(lst)
            lst.append(cur.name)
            cur = cur.parent
        return self

    def find_resource(self, lst):
        """
        try to find a declared build node or a source file
        """
        if isinstance(lst, str):
            lst = [x for x in split_path(lst) if x and x != '.']
        elif issubclass(type(lst), type(self)):
            return lst

        node = self.get_bld().search(lst)
        if node:
            return node

        self = self.get_src()
        node = self.search(lst)
        if node:
            return node

        node = self.find_node(lst)
        if node:
            return node

        return node

    def find_or_declare(self, lst):
        """
        if 'self' is in build directory, try to return an existing node
        if no node is found, go to the source directory
        try to find an existing node in the source directory
        if no node is found, create it in the build directory
        """
        if isinstance(lst, str):
            lst = [x for x in split_path(lst) if x and x != '.']

        node = self.get_bld().search(lst)
        if node:
            if not os.path.isfile(node.abspath()):
                node.sig = None
                try:
                    node.parent.mkdir()
                except:
                    pass
            return node
        self = self.get_src()
        node = self.find_node(lst)
        if node:
            if not os.path.isfile(node.abspath()):
                node.sig = None
                try:
                    node.parent.mkdir()
                except:
                    pass
            return node
        node = self.get_bld().make_node(lst)
        node.parent.mkdir()
        return node

    def declare(self, lst):
        """
        if 'self' is in build directory, try to return an existing node
        if no node is found, create it in the build directory
        """
        if isinstance(lst, str):
            lst = [x for x in split_path(lst) if x and x != '.']

        node = self.get_bld().search(lst)
        if node:
            if not os.path.isfile(node.abspath()):
                node.sig = None
                try:
                    node.parent.mkdir()
                except:
                    pass
            return node
        node = self.get_bld().make_node(lst)
        node.parent.mkdir()
        return node

    def find_dir(self, lst):
        """
        search a folder in the filesystem
        create the corresponding mappings source <-> build directories
        """
        if isinstance(lst, str):
            lst = [x for x in split_path(lst) if x and x != '.']

        node = self.find_node(lst)
        try:
            os.path.isdir(node.abspath())
        except OSError:
            return None
        return node

    # helpers for building things
    def change_ext(self, ext):
        "node of the same path, but with a different extension - hot zone so do not touch"
        name = self.name
        # XXX: is using name.find(".") as done in waf a bug ?
        k = name.rfind('.')
        if k >= 0:
            name = name[:k] + ext
        else:
            name = name + ext

        return self.parent.find_or_declare([name])

    def nice_path(self, env=None):
        "printed in the console, open files easily from the launch directory"
        return self.path_from(self.ctx.launch_node())

    def bldpath(self):
        "path seen from the build directory default/src/foo.cpp"
        return self.path_from(self.ctx.bldnode)

    def srcpath(self):
        "path seen from the source directory ../src/foo.cpp"
        return self.path_from(self.ctx.srcnode)

    def relpath(self):
        "if a build node, bldpath, else srcpath"
        cur = self
        x = id(self.ctx.bldnode)
        while cur.parent:
            if id(cur) == x:
                return self.ctxpath()
            cur = cur.parent
        return self.srcpath()

    def bld_dir(self):
        "build path without the file name"
        return self.parent.bldpath()

    def bld_base(self):
        "build path without the extension: src/dir/foo(.cpp)"
        s = os.path.splitext(self.name)[0]
        return self.bld_dir() + os.sep + s
