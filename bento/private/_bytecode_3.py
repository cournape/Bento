import os
import sys
import builtins
import io
import py_compile
import marshal

if sys.version_info[:2] < (3, 2):
    def _bcompile(file, cfile=None, dfile=None, doraise=False):
        encoding = py_compile.read_encoding(file, "utf-8")
        f = open(file, 'U', encoding=encoding)
        try:
            timestamp = int(os.fstat(f.fileno()).st_mtime)
        except AttributeError:
            timestamp = int(os.stat(file).st_mtime)
        codestring = f.read()
        f.close()
        if codestring and codestring[-1] != '\n':
            codestring = codestring + '\n'
        try:
            codeobject = builtins.compile(codestring, dfile or file,'exec')
        except Exception as err:
            py_exc = py_compile.PyCompileError(err.__class__, err, dfile or file)
            if doraise:
                raise py_exc
            else:
                sys.stderr.write(py_exc.msg + '\n')
                return
        fc = io.BytesIO()
        try:
            fc.write(b'\0\0\0\0')
            py_compile.wr_long(fc, timestamp)
            marshal.dump(codeobject, fc)
            fc.flush()
            fc.seek(0, 0)
            fc.write(py_compile.MAGIC)
            return fc.getvalue()
        finally:
            fc.close()
else:
    import tokenize
    import imp
    import errno
    def _bcompile(file, cfile=None, dfile=None, doraise=False, optimize=-1):
        with tokenize.open(file) as f:
            try:
                timestamp = int(os.fstat(f.fileno()).st_mtime)
            except AttributeError:
                timestamp = int(os.stat(file).st_mtime)
            codestring = f.read()
        try:
            codeobject = builtins.compile(codestring, dfile or file, 'exec',
                                          optimize=optimize)
        except Exception as err:
            py_exc = py_compile.PyCompileError(err.__class__, err, dfile or file)
            if doraise:
                raise py_exc
            else:
                sys.stderr.write(py_exc.msg + '\n')
                return
        if cfile is None:
            if optimize >= 0:
                cfile = imp.cache_from_source(file, debug_override=not optimize)
            else:
                cfile = imp.cache_from_source(file)
        try:
            os.makedirs(os.path.dirname(cfile))
        except OSError as error:
            if error.errno != errno.EEXIST:
                raise
        fc = io.BytesIO()
        try:
            fc.write(b'\0\0\0\0')
            py_compile.wr_long(fc, timestamp)
            marshal.dump(codeobject, fc)
            fc.flush()
            fc.seek(0, 0)
            fc.write(py_compile.MAGIC)
            return fc.getvalue()
        finally:
            fc.close()

def bcompile(file):
    return _bcompile(file, doraise=True)
