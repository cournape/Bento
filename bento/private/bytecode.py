import os
import sys
import marshal

# XXX: implementation details from py_compile
from py_compile import \
    wr_long, MAGIC, PyCompileError
import __builtin__

# Utils to compile .py to .pyc inside zip file
# XXX: this is implementation detail of .pyc, copied from py_compile.py.
# Unfortunately, there is no way that I know of to write the bytecode into a
# string to be used by ZipFile (using compiler is way too slow). Also, the
# py_compile code has not changed much for 10 years.
if sys.version_info[0] < 3:
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO

    def bcompile(source):
        """Return the compiled bytecode from the given filename as a string ."""
        f = open(source, 'U')
        try:
            try:
                timestamp = long(os.fstat(f.fileno()).st_mtime)
            except AttributeError:
                timestamp = long(os.stat(file).st_mtime)
            codestring = f.read()
            f.close()
            if codestring and codestring[-1] != '\n':
                codestring = codestring + '\n'
            try:
                codeobject = __builtin__.compile(codestring, source, 'exec')
            except Exception,err:
                raise PyCompileError(err.__class__, err.args, source)
            fc = StringIO()
            try:
                fc.write('\0\0\0\0')
                wr_long(fc, timestamp)
                fc.write(marshal.dumps(codeobject))
                fc.flush()
                fc.seek(0, 0)
                fc.write(MAGIC)
                return fc.getvalue()
            finally:
                fc.close()
        finally:
            f.close()
else:
    from io import BytesIO

    def bcompile(file, cfile=None, dfile=None, doraise=False):
        encoding = read_encoding(file, "utf-8")
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
            py_exc = PyCompileError(err.__class__, err, dfile or file)
            if doraise:
                raise py_exc
            else:
                sys.stderr.write(py_exc.msg + '\n')
                return
        fc = io.BytesIO()
        try:
            fc.write(b'\0\0\0\0')
            wr_long(fc, timestamp)
            marshal.dump(codeobject, fc)
            fc.flush()
            fc.seek(0, 0)
            fc.write(MAGIC)
            return fc.getvalue()
        finally:
            fc.close()
