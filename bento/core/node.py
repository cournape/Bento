"""
Node class: this is used to build a in-memory representation of the filesystem
in python (as a tree of Nodes). This is mainly used to compute relative
position of files in the filesystem without having to explicitly rely on
absolute paths. This is also more reliable than samepath and relpath, and quite
efficient.

Ripped off from waf (v 1.6), by Thomas Nagy. The cool design is his, bugs most
certainly mine :) We removed a few things which are not useful for bento.
"""
import os, shutil, re, sys, errno

import os.path as op

from bento.compat.api \
    import \
        rename, NamedTemporaryFile
from bento.utils.utils \
    import \
        is_string, extract_exception

def to_list(sth):
    if isinstance(sth, str):
        return sth.split()
    else:
        return sth

exclude_regs = '''
**/*~
**/#*#
**/.#*
**/%*%
**/._*
**/CVS
**/CVS/**
**/.cvsignore
**/SCCS
**/SCCS/**
**/vssver.scc
**/.svn
**/.svn/**
**/BitKeeper
**/.git
**/.git/**
**/.gitignore
**/.bzr
**/.bzrignore
**/.bzr/**
**/.hg
**/.hg/**
**/_MTN
**/_MTN/**
**/.arch-ids
**/{arch}
**/_darcs
**/_darcs/**
**/.DS_Store'''
"""
Ant patterns for files and folders to exclude while doing the
recursive traversal in :py:meth:`waflib.Node.Node.ant_glob`
"""

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
        """Delete the file/folder physically (but not the node)"""
        if getattr(self, 'children', None):
            shutil.rmtree(self.abspath())
            delattr(self, 'children')
        else:
            os.unlink(self.abspath())

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

        self.parent.mkdir()

        if self.name:
            try:
                os.mkdir(self.abspath())
            except OSError:
                e = extract_exception()
                if e.errno != errno.EEXIST:
                    raise

            if not os.path.isdir(self.abspath()):
                raise IOError('%s is not a directory' % self)

            try:
                self.children
            except:
                self.children = {}

        self.cache_isdir = True

    def find_node(self, lst):
        "read the file system, make the nodes as needed"
        if is_string(lst):
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
        if is_string(lst):
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

    def _ant_iter(self, accept=None, maxdepth=25, pats=[], dir=False, src=True, remove=True):
        """
        Semi-private and recursive method used by ant_glob.

        :param accept: function used for accepting/rejecting a node, returns the patterns that can be still accepted in recursion
        :type accept: function
        :param maxdepth: maximum depth in the filesystem (25)
        :type maxdepth: int
        :param pats: list of patterns to accept and list of patterns to exclude
        :type pats: tuple
        :param dir: return folders too (False by default)
        :type dir: bool
        :param src: return files (True by default)
        :type src: bool
        :param remove: remove files/folders that do not exist (True by default)
        :type remove: bool
        """
        dircont = self.listdir()
        dircont.sort()

        try:
            lst = set(self.children.keys())
            if remove:
                for x in lst - set(dircont):
                    del self.children[x]
        except:
            self.children = {}

        for name in dircont:
            npats = accept(name, pats)
            if npats and npats[0]:
                accepted = [] in npats[0]

                node = self.make_node([name])

                isdir = os.path.isdir(node.abspath())
                if accepted:
                    if isdir:
                        if dir:
                            yield node
                    else:
                        if src:
                            yield node

                if getattr(node, 'cache_isdir', None) or isdir:
                    node.cache_isdir = True
                    if maxdepth:
                        for k in node._ant_iter(accept=accept, maxdepth=maxdepth - 1, pats=npats, dir=dir, src=src):
                            yield k
        raise StopIteration

    def ant_glob(self, *k, **kw):
        """
        This method is used for finding files across folders. It behaves like ant patterns:

        * ``**/*`` find all files recursively
        * ``**/*.class`` find all files ending by .class
        * ``..`` find files having two dot characters

        For example::

            def configure(cfg):
                cfg.path.ant_glob('**/*.cpp') # find all .cpp files
                cfg.root.ant_glob('etc/*.txt') # using the filesystem root can be slow
                cfg.path.ant_glob('*.cpp', excl=['*.c'], src=True, dir=False)

        For more information see http://ant.apache.org/manual/dirtasks.html

        The nodes that correspond to files and folders that do not exist will be removed

        :param incl: ant patterns or list of patterns to include
        :type incl: string or list of strings
        :param excl: ant patterns or list of patterns to exclude
        :type excl: string or list of strings
        :param dir: return folders too (False by default)
        :type dir: bool
        :param src: return files (True by default)
        :type src: bool
        :param remove: remove files/folders that do not exist (True by default)
        :type remove: bool
        :param maxdepth: maximum depth of recursion
        :type maxdepth: int
        """

        src = kw.get('src', True)
        dir = kw.get('dir', False)

        excl = kw.get('excl', exclude_regs)
        incl = k and k[0] or kw.get('incl', '**')

        def to_pat(s):
            lst = to_list(s)
            ret = []
            for x in lst:
                x = x.replace('\\', '/').replace('//', '/')
                if x.endswith('/'):
                    x += '**'
                lst2 = x.split('/')
                accu = []
                for k in lst2:
                    if k == '**':
                        accu.append(k)
                    else:
                        k = k.replace('.', '[.]').replace('*','.*').replace('?', '.').replace('+', '\\+')
                        k = '^%s$' % k
                        accu.append(re.compile(k))
                ret.append(accu)
            return ret

        def filtre(name, nn):
            ret = []
            for lst in nn:
                if not lst:
                    pass
                elif lst[0] == '**':
                    ret.append(lst)
                    if len(lst) > 1:
                        if lst[1].match(name):
                            ret.append(lst[2:])
                    else:
                        ret.append([])
                elif lst[0].match(name):
                    ret.append(lst[1:])
            return ret

        def accept(name, pats):
            nacc = filtre(name, pats[0])
            nrej = filtre(name, pats[1])
            if [] in nrej:
                nacc = []
            return [nacc, nrej]

        ret = [x for x in self._ant_iter(accept=accept, pats=[to_pat(incl), to_pat(excl)], maxdepth=25, dir=dir, src=src, remove=kw.get('remove', True))]
        if kw.get('flat', False):
            return ' '.join([x.path_from(self) for x in ret])

        return ret

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

    Every instance of this class must have srcnode/bldnode attributes attached
    to it *outside* __init__ (we need to create nodes before being able to
    refer to them in the instances...)
    """
    _ctx = None
    def is_src(self):
        """
        True if the node is below the source directory
        note: !is_src does not imply is_bld()

        :rtype: bool
        """
        cur = self
        x = id(self._ctx.srcnode)
        y = id(self._ctx.bldnode)
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
        y = id(self._ctx.bldnode)
        while cur.parent:
            if id(cur) == y:
                return True
            cur = cur.parent
        return False

    def get_bld(self):
        """for a src node, will return the equivalent bld node (or self if not possible)"""
        cur = self
        x = id(self._ctx.srcnode)
        y = id(self._ctx.bldnode)
        lst = []
        while cur.parent:
            if id(cur) == y:
                return self
            if id(cur) == x:
                lst.reverse()
                return self._ctx.bldnode.make_node(lst)
            lst.append(cur.name)
            cur = cur.parent
        return self

    def bldpath(self):
        "Path seen from the build directory default/src/foo.cpp"
        return self.path_from(self._ctx.bldnode)

    def srcpath(self):
        "Path seen from the source directory ../src/foo.cpp"
        return self.path_from(self._ctx.srcnode)

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

    def change_ext(self, ext):
        "node of the same path, but with a different extension."
        name = self.name
        # XXX: is using name.find(".") as done in waf a bug ?
        k = name.rfind('.')
        if k >= 0:
            name = name[:k] + ext
        else:
            name = name + ext

        return self.parent.declare([name])

class _NodeContext(object):
    __slot__ = ("srcnode", "bldnode")

def create_first_node(source_path):
    """
    source_path be an absolute path
    """
    root = NodeWithBuild("", None)
    top = root.find_node(source_path)
    if top is None:
        raise IOError("Invalid source_path: %r" % source_path)
    return top

def create_root_with_source_tree(source_path, build_path):
    """
    Both source_path and build_path should be absolute paths
    """
    root = NodeWithBuild("", None)
    top = root.find_node(source_path)
    if top is None:
        raise IOError("Invalid source_path: %r" % source_path)
    build = root.make_node(build_path)

    node_context = _NodeContext()
    node_context.srcnode = top
    node_context.bldnode = build
    NodeWithBuild._ctx = node_context

    return root

def create_base_nodes(source_path=None, build_path=None, run_path=None):
    if source_path is None:
        source_path = os.getcwd()
    if build_path is None:
        build_path = op.join(source_path, "build")
    if run_path is None:
        run_path = os.getcwd()
    root = create_root_with_source_tree(source_path, build_path)
    top_node  = root.find_node(source_path)
    build_node  = root.find_node(build_path)
    run_node = root.find_node(run_path)
    return top_node, build_node, run_node

def find_root(n):
    while n.parent:
        n = n.parent
    return n
