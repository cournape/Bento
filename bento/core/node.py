"""
Node class: this is used to build a in-memory representation of the filesystem
in python (as a tree of Nodes). This is mainly used to compute relative
position of files in the filesystem without having to explicitly rely on
absolute paths. This is also more reliable than samepath and relpath, and quite
efficient.

Ripped off from waf (v 1.6), by Thomas Nagy. The cool design is his, bugs most
certainly mine :) We removed a few things which are not useful for bento.
"""
import os, shutil, re, sys

from bento.compat.api \
    import \
        rename

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
    __slots__ = ('name', 'sig', 'children', 'parent', 'cache_abspath', 'cache_isdir')
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent

        if parent:
            if name in parent.children:
                raise ValueError('node %s exists in the parent files %r already' % (name, parent))
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
        raise NotImplementedError('nodes are not supposed to be copied')

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

    def safe_write(self, data, flags='w'):
        tmp = self.parent.make_node([self.name + ".tmp"])
        tmp.write(data, flags)
        rename(tmp.abspath(), self.abspath())

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

class NodeWithBuild(Node):
    """
    Never create directly, use create_root_with_source_tree function.
    """
    def __init__(self, name, parent):
        super(NodeWithBuild, self).__init__(name, parent)
        # We keep waf naming convention for the members here
        self.srcnode = self.__class__.source_node
        self.bldnode = self.__class__.build_node

    def is_src(self):
        """
        True if the node is below the source directory
        note: !is_src does not imply is_bld()

        :rtype: bool
        """
        cur = self
        x = id(self.srcnode)
        y = id(self.bldnode)
        while cur.parent:
            if id(cur) == y:
                return False
            if id(cur) == x:
                return True
            cur = cur.parent
        return False

    def is_bld(self):
        """
        True if the node is below the build directory
        note: !is_bld does not imply is_src

        :rtype: bool
        """
        cur = self
        y = id(self.bldnode)
        while cur.parent:
            if id(cur) == y:
                return True
            cur = cur.parent
        return False

    def get_src(self):
        """
        Return the equivalent src node (or self if not possible)

        :rtype: :py:class:`waflib.Node.Node`
        """
        cur = self
        x = id(self.srcnode)
        y = id(self.bldnode)
        lst = []
        while cur.parent:
            if id(cur) == y:
                lst.reverse()
                return self.srcnode.make_node(lst)
            if id(cur) == x:
                return self
            lst.append(cur.name)
            cur = cur.parent
        return self

    def get_bld(self):
        """
        Return the equivalent bld node (or self if not possible)

        :rtype: :py:class:`waflib.Node.Node`
        """
        cur = self
        x = id(self.srcnode)
        y = id(self.bldnode)
        lst = []
        while cur.parent:
            if id(cur) == y:
                return self
            if id(cur) == x:
                lst.reverse()
                return self.bldnode.make_node(lst)
            lst.append(cur.name)
            cur = cur.parent
        return self

    def bldpath(self):
        "Path seen from the build directory default/src/foo.cpp"
        return self.path_from(self.bldnode)

    def srcpath(self):
        "Path seen from the source directory ../src/foo.cpp"
        return self.path_from(self.srcnode)

def create_root_with_source_tree(source_path, build_path):
    """
    Both source_path and build_path should be absolute paths
    """
    NodeWithBuild.source_node = None
    NodeWithBuild.build_node = None

    root = NodeWithBuild("", None)
    top = root.make_node(source_path)
    build = root.make_node(build_path)

    NodeWithBuild.source_node = top
    NodeWithBuild.build_node = build
    for node in [root, top, build]:
        node.srcnode = top
        node.bldnode = build

    return root
